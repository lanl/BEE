import re
import sys


results = []
for fname in sys.argv[1:]:
    pe_count = 0
    times = []
    with open(fname) as fp:
        for line in fp:
            # Check for the PE count
            m_pe_count = re.match(r'Running on (\d+) MPI PE\(s\)', line)
            if m_pe_count:
                pe_count = int(m_pe_count.group(1))
                continue
            # Check for an End cyle line
            if not line.startswith('End cycle'):
                continue
            _, _, _, wall = line.split(',')
            _, time = wall.split('=')
            time = float(time.strip())
            times.append(time)
    results.append({
        'pe_count': pe_count,
        'times': times,
    })
print(results)
