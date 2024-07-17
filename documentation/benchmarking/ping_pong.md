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
<tr><td></td><td colspan="3" style="text-align:center;">Average messages Per Second</td></tr>
<tr><td></td><td style="text-align:center;">TCP</td><td style="text-align:center;">UDP</td><td style="text-align:center;">UDS</td></tr>
</thead>
<tbody>
<tr><td>No logging                     </td> <td> 1611.503306 </td> <td> 2238.675771 </td> <td> 1798.064022 </td> </tr>
<tr><td>console logging only           </td> <td> 1473.336817 </td> <td> 1979.069276 </td> <td> 1590.829693 </td> </tr>
<tr><td>console and file (no buffering)</td> <td> 1380.600203 </td> <td> 1778.328000 </td> <td> 1468.579149 </td> </tr>
<tr><td>file only (no buffering)       </td> <td> 1432.214038 </td> <td> 1859.828080 </td> <td> 1536.075089 </td> </tr>
<tr><td>file only (buffering 500)      </td> <td> 1494.101939 </td> <td> 2031.509366 </td> <td> 1643.041305 </td> </tr>
<tr><td>file only (buffering 1000)     </td> <td> 1495.420158 </td> <td> 2039.206482 </td> <td> 1646.153790 </td> </tr>
<tr><td>file only (buffering 1500)     </td> <td> 1500.154039 </td> <td> 2046.740385 </td> <td> 1646.950333 </td> </tr>
<tr><td>file only (buffering 2000)     </td> <td> 1492.454323 </td> <td> 2032.287148 </td> <td> 1654.242241 </td> </tr>
<tr><td>file only (buffering 2500)     </td> <td> 1500.021623 </td> <td> 2040.157801 </td> <td> 1653.660265 </td> </tr>
</tbody>
</table>

## Conclusion

Unsurprisingly, just having a single log line in code cost us at least 100
messages per second, when compared to having none at all. 

Logging is expensive under the best of circumstance, it is however a necessary evil.

Buffering and having the option to have only console or only file logging
improves the situation. But these are user managed options.

### Advice to users

Test with file logging only, and zero buffering fist. As your systems mature,
and gain stability, increase the log buffer to an optimal level for your
production servers.

## Detailed Results and how I got them

---
### No logging

For this, I removed the log line `log.info(f"{request_uuid}")` from the
`app_ping` function in the `pong` server.

- Run pong server with: `python -m ping_pong.pong -i 0 -lco`
- Run ping client with: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.193003 = 1614.725626 messages/second
    run #2: 10000/6.220420 = 1607.608476 messages/second
    run #3: 10000/6.241004 = 1602.306254 messages/second
    run #4: 10000/6.189596 = 1615.614313 messages/second
    run #5: 10000/6.183291 = 1617.261859 messages/second
Average: 1611.503306

Doing UDP run:
UDP report:
    run #1: 10000/4.457023 = 2243.649985 messages/second
    run #2: 10000/4.449643 = 2247.371340 messages/second
    run #3: 10000/4.480360 = 2231.963508 messages/second
    run #4: 10000/4.465243 = 2239.520009 messages/second
    run #5: 10000/4.482548 = 2230.874014 messages/second
Average: 2238.675771

Doing UDS run:
UDS report:
    run #1: 10000/5.598277 = 1786.263925 messages/second
    run #2: 10000/5.589091 = 1789.199564 messages/second
    run #3: 10000/5.557773 = 1799.281778 messages/second
    run #4: 10000/5.516825 = 1812.636880 messages/second
    run #5: 10000/5.546503 = 1802.937962 messages/second
Average: 1798.064022
```

---
### Console logging only
- Run pong server: `python -m ping_pong.pong -i 0 -lco`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.789426 = 1472.878609 messages/second
    run #2: 10000/6.786726 = 1473.464502 messages/second
    run #3: 10000/6.766786 = 1477.806373 messages/second
    run #4: 10000/6.799163 = 1470.769178 messages/second
    run #5: 10000/6.794561 = 1471.765423 messages/second
Average: 1473.336817

Doing UDP run:
UDP report:
    run #1: 10000/5.055613 = 1977.999665 messages/second
    run #2: 10000/5.056632 = 1977.601071 messages/second
    run #3: 10000/5.067535 = 1973.346051 messages/second
    run #4: 10000/5.037812 = 1984.988677 messages/second
    run #5: 10000/5.046909 = 1981.410915 messages/second
Average: 1979.069276

Doing UDS run:
UDS report:
    run #1: 10000/6.241269 = 1602.238216 messages/second
    run #2: 10000/6.319802 = 1582.327931 messages/second
    run #3: 10000/6.284154 = 1591.304182 messages/second
    run #4: 10000/6.296437 = 1588.199809 messages/second
    run #5: 10000/6.288998 = 1590.078325 messages/second
Average: 1590.829693
```

---
### Both file and console logging, without any file write buffering
Make sure no buffering is set with environment variables with: `unset ECOENV_LOG_BUF_SIZE`

- Run pong server: `python -m ping_pong.pong -i 0`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/7.220669 = 1384.913220 messages/second
    run #2: 10000/7.309463 = 1368.089479 messages/second
    run #3: 10000/7.228143 = 1383.481244 messages/second
    run #4: 10000/7.190710 = 1390.683298 messages/second
    run #5: 10000/7.268320 = 1375.833774 messages/second
Average: 1380.600203

Doing UDP run:
UDP report:
    run #1: 10000/5.634395 = 1774.813395 messages/second
    run #2: 10000/5.607999 = 1783.167262 messages/second
    run #3: 10000/5.655624 = 1768.151512 messages/second
    run #4: 10000/5.624814 = 1777.836615 messages/second
    run #5: 10000/5.593870 = 1787.671216 messages/second
Average: 1778.328000

Doing UDS run:
UDS report:
    run #1: 10000/6.766883 = 1477.785306 messages/second
    run #2: 10000/6.865205 = 1456.620737 messages/second
    run #3: 10000/6.845856 = 1460.737737 messages/second
    run #4: 10000/6.776461 = 1475.696468 messages/second
    run #5: 10000/6.793222 = 1472.055499 messages/second
Average: 1468.579149
```


### File logging only, without buffering
Make sure no buffering is set with environment variables with: `unset ECOENV_LOG_BUF_SIZE`

- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.982703 = 1432.110078 messages/second
    run #2: 10000/6.977115 = 1433.257054 messages/second
    run #3: 10000/6.997666 = 1429.047991 messages/second
    run #4: 10000/6.964311 = 1435.892170 messages/second
    run #5: 10000/6.989278 = 1430.762895 messages/second
Average: 1432.214038

Doing UDP run:
UDP report:
    run #1: 10000/5.362210 = 1864.902828 messages/second
    run #2: 10000/5.423644 = 1843.778726 messages/second
    run #3: 10000/5.389942 = 1855.307441 messages/second
    run #4: 10000/5.375493 = 1860.294451 messages/second
    run #5: 10000/5.333740 = 1874.856953 messages/second
Average: 1859.828080

Doing UDS run:
UDS report:
    run #1: 10000/6.576170 = 1520.641915 messages/second
    run #2: 10000/6.518515 = 1534.091621 messages/second
    run #3: 10000/6.476879 = 1543.953476 messages/second
    run #4: 10000/6.477293 = 1543.854918 messages/second
    run #5: 10000/6.502654 = 1537.833514 messages/second
Average: 1536.075089
```

#### Log buffer set to 500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.679193 = 1497.186754 messages/second
    run #2: 10000/6.650113 = 1503.733777 messages/second
    run #3: 10000/6.684015 = 1496.106661 messages/second
    run #4: 10000/6.751038 = 1481.253772 messages/second
    run #5: 10000/6.701386 = 1492.228732 messages/second
Average: 1494.101939

Doing UDP run:
UDP report:
    run #1: 10000/4.943627 = 2022.806450 messages/second
    run #2: 10000/4.911420 = 2036.071031 messages/second
    run #3: 10000/4.895939 = 2042.508992 messages/second
    run #4: 10000/4.930618 = 2028.143437 messages/second
    run #5: 10000/4.930925 = 2028.016920 messages/second
Average: 2031.509366

Doing UDS run:
UDS report:
    run #1: 10000/6.109104 = 1636.901208 messages/second
    run #2: 10000/6.052914 = 1652.096703 messages/second
    run #3: 10000/6.130072 = 1631.302130 messages/second
    run #4: 10000/6.061289 = 1649.813957 messages/second
    run #5: 10000/6.078685 = 1645.092525 messages/second
Average: 1643.041305
```

#### Log buffer set to 1000
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=1000`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.677131 = 1497.649238 messages/second
    run #2: 10000/6.672815 = 1498.617883 messages/second
    run #3: 10000/6.705495 = 1491.314322 messages/second
    run #4: 10000/6.688124 = 1495.187663 messages/second
    run #5: 10000/6.691955 = 1494.331682 messages/second
Average: 1495.420158

Doing UDP run:
UDP report:
    run #1: 10000/4.920495 = 2032.315857 messages/second
    run #2: 10000/4.894890 = 2042.946762 messages/second
    run #3: 10000/4.897366 = 2041.914027 messages/second
    run #4: 10000/4.903462 = 2039.375312 messages/second
    run #5: 10000/4.903210 = 2039.480451 messages/second
Average: 2039.206482

Doing UDS run:
UDS report:
    run #1: 10000/6.124416 = 1632.808745 messages/second
    run #2: 10000/6.100397 = 1639.237698 messages/second
    run #3: 10000/6.035756 = 1656.793289 messages/second
    run #4: 10000/6.075332 = 1646.000484 messages/second
    run #5: 10000/6.038907 = 1655.928736 messages/second
Average: 1646.153790
```

#### Log buffer set to 1500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=1500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.677380 = 1497.593351 messages/second
    run #2: 10000/6.681651 = 1496.636176 messages/second
    run #3: 10000/6.678937 = 1497.244330 messages/second
    run #4: 10000/6.646789 = 1504.485800 messages/second
    run #5: 10000/6.645355 = 1504.810537 messages/second
Average: 1500.154039

Doing UDP run:
UDP report:
    run #1: 10000/4.927516 = 2029.420081 messages/second
    run #2: 10000/4.904895 = 2038.779459 messages/second
    run #3: 10000/4.904961 = 2038.752338 messages/second
    run #4: 10000/4.858417 = 2058.283506 messages/second
    run #5: 10000/4.834499 = 2068.466542 messages/second
Average: 2046.740385

Doing UDS run:
UDS report:
    run #1: 10000/6.063632 = 1649.176677 messages/second
    run #2: 10000/6.036841 = 1656.495378 messages/second
    run #3: 10000/6.052730 = 1652.147066 messages/second
    run #4: 10000/6.092169 = 1641.451604 messages/second
    run #5: 10000/6.114409 = 1635.480943 messages/second
Average: 1646.950333
```

#### Log buffer set to 2000
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=2000`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.651824 = 1503.346961 messages/second
    run #2: 10000/6.706876 = 1491.007166 messages/second
    run #3: 10000/6.717338 = 1488.684856 messages/second
    run #4: 10000/6.707558 = 1490.855632 messages/second
    run #5: 10000/6.718728 = 1488.376997 messages/second
Average: 1492.454323

Doing UDP run:
UDP report:
    run #1: 10000/4.934235 = 2026.656410 messages/second
    run #2: 10000/4.897964 = 2041.664661 messages/second
    run #3: 10000/4.909529 = 2036.855297 messages/second
    run #4: 10000/4.929768 = 2028.493175 messages/second
    run #5: 10000/4.931535 = 2027.766196 messages/second
Average: 2032.287148

Doing UDS run:
UDS report:
    run #1: 10000/6.018166 = 1661.635679 messages/second
    run #2: 10000/6.010865 = 1663.654109 messages/second
    run #3: 10000/6.060141 = 1650.126511 messages/second
    run #4: 10000/6.075637 = 1645.917955 messages/second
    run #5: 10000/6.061058 = 1649.876952 messages/second
Average: 1654.242241
```

#### Log buffer set to 2500
- Set log buffer : `export ECOENV_LOG_BUF_SIZE=2500`
- Run pong server: `python -m ping_pong.pong -i 0 -lfo`
- Run ping client: `python -m benchmarking.ping_pong.ping 10000 5`
```
Doing TCP run:
TCP report:
    run #1: 10000/6.618086 = 1511.010785 messages/second
    run #2: 10000/6.651019 = 1503.528901 messages/second
    run #3: 10000/6.652236 = 1503.253992 messages/second
    run #4: 10000/6.697071 = 1493.190176 messages/second
    run #5: 10000/6.715356 = 1489.124264 messages/second
Average: 1500.021623

Doing UDP run:
UDP report:
    run #1: 10000/4.927903 = 2029.260748 messages/second
    run #2: 10000/4.880846 = 2048.825074 messages/second
    run #3: 10000/4.892831 = 2043.806634 messages/second
    run #4: 10000/4.915149 = 2034.526437 messages/second
    run #5: 10000/4.891482 = 2044.370114 messages/second
Average: 2040.157801

Doing UDS run:
UDS report:
    run #1: 10000/6.082242 = 1644.130435 messages/second
    run #2: 10000/6.040191 = 1655.576714 messages/second
    run #3: 10000/6.052012 = 1652.343024 messages/second
    run #4: 10000/6.048305 = 1653.355863 messages/second
    run #5: 10000/6.013608 = 1662.895289 messages/second
Average: 1653.660265
```
