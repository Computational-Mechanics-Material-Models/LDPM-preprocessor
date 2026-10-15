from pathlib import Path


def mkVtk_LDPMCSL_reinforcement(geoName, tempPath, nodes, elements, diameter=1.0):
    if not nodes or not elements:
        return None
    path = Path(tempPath) / (geoName + "-para-reinforcement.000.vtk")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        diameter = float(diameter)
    except (TypeError, ValueError):
        diameter = 0.0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# vtk DataFile Version 2.0\n")
        handle.write("Reinforcement line mesh\n")
        handle.write("ASCII\n")
        handle.write("\n")
        handle.write("DATASET POLYDATA\n")
        handle.write("POINTS %d double\n" % len(nodes))
        for point in nodes:
            handle.write(
                "%.10g %.10g %.10g\n"
                % (float(point[0]), float(point[1]), float(point[2]))
            )
        handle.write("\n")
        handle.write("LINES %d %d\n" % (len(elements), len(elements) * 3))
        for element in elements:
            handle.write("2 %d %d\n" % (int(element[0]), int(element[1])))
        handle.write("\n")
        handle.write("CELL_DATA %d\n" % len(elements))
        handle.write("SCALARS Diameter float 1\n")
        handle.write("LOOKUP_TABLE default\n")
        for _ in elements:
            handle.write("%.10g\n" % diameter)
        handle.write("SCALARS Length float 1\n")
        handle.write("LOOKUP_TABLE default\n")
        for element in elements:
            n1 = int(element[0])
            n2 = int(element[1])
            p1 = nodes[n1]
            p2 = nodes[n2]
            length = (
                (float(p1[0]) - float(p2[0])) ** 2
                + (float(p1[1]) - float(p2[1])) ** 2
                + (float(p1[2]) - float(p2[2])) ** 2
            ) ** 0.5
            handle.write("%.10g\n" % length)
    return str(path)
