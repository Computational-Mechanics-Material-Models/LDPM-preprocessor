# Workarounds for some known issues

### Problem for Win10 + VS2015

gmesh works but tetgen reports lack file "vcruntime140_1d.dll"
Solution: copy vcruntime140_1d.dll file with tetgen.exe to the work direction.
Reference link: https://www.dll-files.com/download/868fd5f1ab2d50204c6b046fe172d4b8/vcruntime140_1d.dll.html?c=ZU1VRnJyc3lOeWxMbEQ2cDR3V1NQUT09

- By Lei Shen, 06/17/2021 

### Instructions for MacOS users

1. To use *chrono-preprocessor* in *FreeCAD*, first clone the repo and copy it to the right place, see [instruction](https://wiki.freecad.org/How_to_install_additional_workbenches#Manual_Installation_2). 
2. Make sure [*Gmsh*](https://gmsh.info/) is installed.
3. Make sure [*tetgen*](https://wias-berlin.de/software/index.jsp?id=TetGen&lang=1) works. **Note that the executable file [tetgen](https://github.com/Concrete-Chrono-Development/chrono-preprocessor/blob/main/freecad/ldpmWorkbench/tetgen/tetgen) in this directory does NOT work for MacOS.** You need to compile the source code on your MacOS machine and generate an executable file of `tetgen` and replace the original not-working file with this newly-generated one. If you still see an error saying `Tetgen failed during tetrahedralization.`, it is probably because `tetgen` is not properly called. You need to do `chmod` to make `tetgen` an executable file.

- By [Tianju Xue](https://tianjuxue.github.io/), 08/28/2023

