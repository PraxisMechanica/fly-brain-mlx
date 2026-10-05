import brian2 as b

from .observer_stream import PHASE_FIELDS, StreamShape


def array_name(
    owner: b.NeuronGroup | b.StateMonitor | b.SpikeGeneratorGroup, name: str
) -> str:
    return b.device.get_array_name(owner.variables[name], access_data=False)


def snapshot_code(
    group: b.NeuronGroup,
    source: b.SpikeGeneratorGroup | None,
    pathways: tuple[b.Synapses, ...],
    shape: StreamShape,
) -> str:
    code = [
        'obs_q(step);',
        'obs_q(defaultclock.timestep[0]);',
        'obs_d(defaultclock.t[0]);',
        f'obs_i({array_name(source, "_lastindex")}[0]);' if source else 'obs_i(-1);',
    ]
    for owner, size in ((group, shape.neurons), (source, shape.channels)):
        if owner is None:
            code.append('obs_q(0);')
        else:
            spikes = array_name(owner, '_spikespace')
            code.extend(
                (
                    f'obs_q({spikes}[{size}]);',
                    f'obs_write({spikes}, {spikes}[{size}] * sizeof(int32_t));',
                )
            )
    for synapses in pathways:
        name = synapses.pre.name
        code.append(f'obs_q({name}.queue.size());')
        code.append(f'for(const auto* queue : {name}.queue) {{')
        code.extend(
            (
                'obs_i(queue->offset);',
                'obs_q(queue->queue.size());',
                'for(const auto& slot : queue->queue) {',
                'obs_q(slot.size());',
                'obs_write(slot.data(), slot.size() * sizeof(int32_t));',
                '}',
                '}',
            )
        )
        code.extend(
            (
                f'obs_q({name}.all_peek.size());',
                f'obs_write({name}.all_peek.data(), {name}.all_peek.size() * sizeof(int32_t));',
            )
        )
    return '\n'.join(code)


def phase_code(monitors: tuple[b.StateMonitor, ...], shape: StreamShape) -> str:
    if not shape.block_size:
        return ''
    code = [
        f'if(obs_step % {shape.block_size} == 0 || obs_step == {shape.steps}) {{',
        f'const size_t rows = {array_name(monitors[0], "t")}.size();',
        'obs_q(2); obs_q(obs_step - rows); obs_q(rows);',
    ]
    for monitor, (_, fields) in zip(monitors, PHASE_FIELDS, strict=True):
        times = array_name(monitor, 't')
        code.append(f'obs_write({times}.data(), rows * sizeof(double));')
        for field in fields:
            array = array_name(monitor, field)
            code.append('for(size_t row=0; row<rows; ++row) {')
            if field == 'not_refractory':
                code.extend(
                    (
                        f'for(size_t neuron=0; neuron<{shape.neurons}; ++neuron) {{',
                        f'obs_booleans[neuron] = {array}(row, neuron) ? 1 : 0;',
                        '}',
                        'obs_write(obs_booleans.data(), obs_booleans.size());',
                    )
                )
            else:
                code.append(
                    f'obs_write({array}(row).data(), {shape.neurons} * sizeof(double));'
                )
            code.extend(('}', f'{array}.resize(0, {shape.neurons});'))
        code.extend((f'{times}.clear();', f'{array_name(monitor, "N")}[0] = 0;'))
    code.extend(('obs_finish();', '}'))
    return '\n'.join(code)


def install(
    network: b.Network,
    group: b.NeuronGroup,
    source: b.SpikeGeneratorGroup | None,
    pathways: tuple[b.Synapses, ...],
    monitors: tuple[b.StateMonitor, ...],
    shape: StreamShape,
) -> None:
    b.device.headers.append('<zlib.h>')
    b.device.libraries.append('z')
    setup = """
static_assert(sizeof(double)==8 && sizeof(int32_t)==4 && sizeof(uint64_t)==8, "Observer scalar widths differ");
static uint32_t obs_crc = 0xffffffffu;
static auto obs_write = [](const void* pointer, size_t size) {
    if(size) {
        const auto* data = static_cast<const unsigned char*>(pointer);
        std::cout.write(reinterpret_cast<const char*>(data), size);
        obs_crc = static_cast<uint32_t>(crc32_z(obs_crc ^ 0xffffffffu, data, size)) ^ 0xffffffffu;
    }
};
static auto obs_q = [](uint64_t value) { obs_write(&value, sizeof(value)); };
static auto obs_i = [](int32_t value) { obs_write(&value, sizeof(value)); };
static auto obs_d = [](double value) { obs_write(&value, sizeof(value)); };
static auto obs_finish = []() {
    const uint32_t value = obs_crc ^ 0xffffffffu;
    std::cout.write(reinterpret_cast<const char*>(&value), sizeof(value));
    obs_crc = 0xffffffffu;
};
static uint64_t obs_step = 0;
"""
    setup += f'static std::vector<uint8_t> obs_booleans({shape.neurons});\n'
    header = (
        'obs_write("FBQOBS01", 8);\n'
        + '\n'.join(
            f'obs_q({value});'
            for value in (
                shape.neurons,
                shape.steps,
                shape.channels,
                len(pathways),
                shape.block_size,
            )
        )
        + '\nobs_finish();\n'
    )
    snapshot = (
        'static auto obs_snapshot = [](uint64_t step) {\n'
        + snapshot_code(group, source, pathways, shape)
        + '\n};\n'
    )
    callback = (
        f'{network.name}.add(&defaultclock, +[]() {{\nobs_q(1); obs_snapshot(obs_step); obs_finish();\n++obs_step;\n'
        + phase_code(monitors, shape)
        + '\n});\n'
    )
    b.device.insert_code('before_network_run', setup + header + snapshot + callback)
    final = [f'obs_q(3); obs_snapshot({shape.steps});']
    for name in ('v', 'g', 'lastspike', 'not_refractory'):
        array = array_name(group, name)
        if name == 'not_refractory':
            final.extend(
                (
                    f'for(size_t neuron=0; neuron<{shape.neurons}; ++neuron) {{',
                    f'obs_booleans[neuron] = {array}[neuron] ? 1 : 0;',
                    '}',
                    'obs_write(obs_booleans.data(), obs_booleans.size());',
                )
            )
        else:
            final.append(f'obs_write({array}, {shape.neurons} * sizeof(double));')
    final.append('obs_finish(); std::cout.flush();')
    b.device.insert_code('after_network_run', '\n'.join(final))
