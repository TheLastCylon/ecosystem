# Ping Pong

These test were performed on my development machine. For what its worth:

- **CPU**: Intel® Core™ i5-8400 CPU @ 2.80GHz × 6
- **OS**: Linux Mint, Kernel 5.15.0-101-generic x86_64

## Purpose 
- Test response times
- Test the effect of logging on response times

## Code
Located in `benchmarking/ping_pong` of this repository.

Files:

| purpose | link                                            |
|---------|-------------------------------------------------|
| DTOs    | [dtos.py](../../benchmarking/ping_pong/dtos.py) |
| Client  | [ping.py](../../benchmarking/ping_pong/ping.py) |
| Server  | [pong.py](../../benchmarking/ping_pong/pong.py) |

## Result summary

<table>
<thead>
<tr>
    <td rowspan="3">Logging Conditions</td>
    <td colspan="5" style="text-align:center;">Average messages Per Second</td>
</tr>
<tr>
    <td style="text-align:center;" colspan="2">TCP</td>
    <td style="text-align:center;" rowspan="2">UDP</td>
    <td style="text-align:center;" colspan="2">UDS</td>
</tr>
<tr>
    <td style="text-align:center;">Transient</td>
    <td style="text-align:center;">Persisted</td>
    <td style="text-align:center;">Transient</td>
    <td style="text-align:center;">Persisted</td>
</tr>
</thead>
<tbody>
<tr><td>No logging                     </td> <td> 3292.280093 </td> <td> 8593.334501 </td> <td> 8924.253328 </td> <td> 4245.500628 </td> <td> 9722.022167 </td> </tr>
<tr><td>console logging only           </td> <td> 2864.470734 </td> <td> 6448.129065 </td> <td> 6634.411518 </td> <td> 3379.348335 </td> <td> 7126.949054 </td> </tr>
<tr><td>console and file (no buffering)</td> <td> 2527.350010 </td> <td> 5223.578301 </td> <td> 5302.335473 </td> <td> 2884.056522 </td> <td> 5639.020187 </td> </tr>
<tr><td>file only (no buffering)       </td> <td> 2706.511528 </td> <td> 5647.033629 </td> <td> 5816.822225 </td> <td> 3126.526107 </td> <td> 6214.911204 </td> </tr>
<tr><td>file only (buffering 500)      </td> <td> 2941.813155 </td> <td> 6515.288889 </td> <td> 6698.015409 </td> <td> 3570.469934 </td> <td> 7064.599933 </td> </tr>
<tr><td>file only (buffering 1000)     </td> <td> 2939.847401 </td> <td> 6502.788445 </td> <td> 6646.758707 </td> <td> 3584.932382 </td> <td> 7131.265217 </td> </tr>
<tr><td>file only (buffering 1500)     </td> <td> 2827.720892 </td> <td> 6263.412670 </td> <td> 6258.180477 </td> <td> 3561.896277 </td> <td> 7099.615760 </td> </tr>
<tr><td>file only (buffering 2000)     </td> <td> 2939.451701 </td> <td> 6535.053231 </td> <td> 6741.050982 </td> <td> 3576.607269 </td> <td> 7112.602463 </td> </tr>
<tr><td>file only (buffering 2500)     </td> <td> 2827.537651 </td> <td> 6534.726138 </td> <td> 6737.618496 </td> <td> 3562.466431 </td> <td> 7117.847145 </td> </tr>
</tbody>
</table>

## Conclusion

Unsurprisingly, just having a single log line in code has a significant cost,
when compared to having none at all. 

Logging is expensive under the best of circumstance, it is however a necessary
evil.

Buffering and having the option to have only console or only file logging
improves the situation. But these are user managed options.

### Advice to users

Test with file logging only, and zero buffering fist. As your systems mature,
and gain stability, increase the log buffer to an optimal level for your
production servers.

## Detailed on how to run each benchmark for yourself.

---
### No logging

For this, I removed the log line `log.info(f"{request_uuid}")` from the
`app_ping` function in the `pong` server, then:

- Make sure no buffering is set, I do that with: `unset ECOENV_LOG_BUF_SIZE`
- Run pong server with: `python -m ping_pong.pong -i 0 -lco`
- Run ping client with: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Console logging only
- Make sure no buffering is set: `unset ECOENV_LOG_BUF_SIZE`
- Run pong server: `python -m ping_pong.pong -i 0 -lco`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Both file and console logging, without any file write buffering

- Make sure no buffering is set: `unset ECOENV_LOG_BUF_SIZE`
- Run pong server: `python -m ping_pong.pong -i 0`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### File logging only, without buffering

- Make sure no buffering is set: `unset ECOENV_LOG_BUF_SIZE`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Log buffer set to 500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Log buffer set to 1000
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=1000`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Log buffer set to 1500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=1500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Log buffer set to 2000
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=2000`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`

---
### Log buffer set to 2500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=2500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
