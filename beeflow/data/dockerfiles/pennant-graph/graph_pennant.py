"""Graph the output of a PENNANT workflow."""
import re
import sys
import matplotlib.pyplot as plt


results = []
for fname in sys.argv[1:]:
    pe_count = 0
    times = []
    with open(fname, encoding='utf-8') as fp:
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
        'average_wall_time': sum(times) / len(times),
    })

# The node counts
x = [str(result['pe_count']) for result in results]
# Average wall for cycle
y = [result['average_wall_time'] for result in results]
fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_title('PENNANT Workflow Run')
ax.set_xlabel('Node count')
ax.set_ylabel('Average wall time for cycle')
# Save to a png file
fig.savefig('graph.png')

# Ignore C0103: This is just a simple script, not all globals should be UPPER_CASE here
# pylama:ignore=C0103
