## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ===========================================================================
##
## Description coming soon...
##
## ===========================================================================

# pyright: reportMissingImports=false
from pathlib import Path
import FreeCAD as App
from femtools import membertools

def mkChronoInput(elementType, analysisName, materialProps, materialPropsDesc, materialPropsVals, simProps, simPropsValues, \
    nodesFilename, elemFilename, facetsFilename, geoName, outDir, outName):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - elementType:      The type of element that will be used
    - analysisName:     The name of the analysis
    - materialProps:    The names of the material properties
    - materialPropsVals:The values of the material properties
    - simProps:         The names of the simulation properties
    - simPropsValues:   The values of the simulation properties
    - nodesFilename:    The name of the file containing the nodes
    - elemFilename:     The name of the file containing the tets
    - facetsFilename:   The name of the file containing the facets
    - geoName:          The name of the geometry
    - outDir:           The output directory
    - outName:          The output name
    --------------------------------------------------------------------------
    ### Outputs ###
    - An input file for Project Chrono
    --------------------------------------------------------------------------
    """


    doc = App.ActiveDocument

    if elementType == 'LDPM':
        analysis = doc.getObject("LDPManalysis")
    elif elementType == 'CSL':
        analysis = doc.getObject("CSLanalysis")

    with open(Path(outDir + outName + '/' + geoName + '-chrono.cpp'),"w") as output_file:

        output_file.write("""
// ================================================================================
// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor
//
// Copyright (c) 2023 
// All rights reserved. 
//
// Use of the code that generated this file is governed by a BSD-style license that
// can be found in the LICENSE file at the top level of the distribution and at
// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
//
// ================================================================================
// Chrono Input File
// ================================================================================
// 
// LDPM Workbench developed by Northwestern University
//
// ================================================================================
        \n""")

        output_file.write("""
#include <chrono/physics/ChSystemSMC.h>
#include <chrono/physics/ChLinkMate.h>
#include <chrono/physics/ChBodyEasy.h>
#include <chrono/solver/ChIterativeSolverLS.h>
#include <chrono/timestepper/ChTimestepper.h>

#include "chrono/fea/ChElementBeamEuler.h"
#include "chrono/fea/ChBuilderBeam.h"
#include "chrono/fea/ChMesh.h"
#include "chrono/fea/ChLinkPointFrame.h"
#include "chrono/fea/ChLinkDirFrame.h"
#include "chrono/assets/ChVisualShapeFEA.h"
#include <chrono_irrlicht/ChVisualSystemIrrlicht.h>
#include <chrono/core/ChStream.h>
#include <chrono/fea/ChMeshExporter.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cstdlib>
#include <string>
#include <typeinfo>


using namespace chrono;
using namespace chrono::fea;

int main(int argc, char** argv) {
        \n""")

        # Store solver parameters
        output_file.write('\n    // Solver Parameters\n')
        for x in range(len(simProps)):    
            output_file.write('    double ' + simProps[x] + ' = ' + str(simPropsValues[x]) + ';\n')
        output_file.write('\n')

        # Store material parameters
        output_file.write('    // ' + elementType + ' Material Parameters\n')
        for x in range(len(materialProps)):
            output_file.write('    double ' + materialProps[x] + ' = ' + str(materialPropsVals[x]) + ';\n')
        output_file.write('\n')

        # Store files to read
        output_file.write('    // Reference Data Files\n')
        output_file.write('    std::stream nodesFilename = "' + nodesFilename + '";\n')
        output_file.write('    std::stream elemFilename = "' + elemFilename + '";\n')
        output_file.write('    std::stream facetsFilename = "' + facetsFilename + '";\n')
        output_file.write('    std::ifstream nodesFile(nodesFilename);\n')
        output_file.write('    std::ifstream elemFile(elemFilename);\n')
        output_file.write('    std::ifstream facetsFile(facetsFilename);\n')
        output_file.write('\n')

        # Create the LDPM element mesh
        if elementType == 'LDPM':
            
            output_file.write("""
    // Create a tetrahedra mesh object
    std::shared_ptr<ChMesh> mesh(new ChMesh);

    // Add nodes to the mesh 
    if (nodesFile.is_open()) {	
        ChVector<> pos;
        double x, y, z;
        unsigned int idnode=0;
        while (nodesFile >> pos[0] >> pos[1]>> pos[2]) {
            auto mnode= chrono_types::make_shared<ChNodeFEAxyzrot>(ChFrame<>(ChVector<>(pos[0], pos[1], pos[2])));
            //auto mnode = chrono_types::make_shared<ChNodeFEAxyzrot>(ChFrame<>(pos));
                mnode->SetIndex(idnode);
                my_mesh->AddNode(mnode);
                ++idnode;    		
        }
    }
    else{
        throw ChException("ERROR opening nodes info file: " + std::string(nodesFilename) + ");
        exit(EXIT_FAILURE);
    }
    auto nodenum=my_mesh->GetNnodes();
    std::cout << "nodenum " << nodenum<<std::endl;
    for (int i=0; i<nodenum; ++i){
        auto node = std::dynamic_pointer_cast<ChNodeFEAxyzrot>(my_mesh->GetNode(i));    	
        auto x=node->GetPos().x();
        auto y=node->GetPos().y();
        auto z=node->GetPos().z();
        std::cout<<i<<".Node "<< node->GetIndex()<<" x : "<< x <<" y : "<< y <<" z : "<< z << std::endl;
    }

    // Add elements to the mesh
    int n1, n2, n3, n4;
    while (elemFilename >> n1 >> n2 >> n3 >> n4) {
        auto node1 = std::static_pointer_cast<ChNodeFEAxyz>(mesh->GetNode(n1));
        auto node2 = std::static_pointer_cast<ChNodeFEAxyz>(mesh->GetNode(n2));
        auto node3 = std::static_pointer_cast<ChNodeFEAxyz>(mesh->GetNode(n3));
        auto node4 = std::static_pointer_cast<ChNodeFEAxyz>(mesh->GetNode(n4));
        mesh->AddElement(std::make_shared<ChElementLDPM>(node1, node2, node3, node4));
    }
            \n""")


        # Create the CSL element mesh
        elif elementType == 'CSL':
            
            output_file.write("""


    auto msection = chrono_types::make_shared<ChBeamSectionEulerAdvanced>();

    double beam_wy = 0.1;
    double beam_wz = 0.50;    
    //msection->SetAsRectangularSection(beam_wy, beam_wz);
    double radius=1.;
    msection->SetAsCircularSection(radius);
    msection->SetYoungModulus(3.0e4);
    msection->SetGshearModulus(3.0e4/(1.+0.2)/2.0);
    msection->SetBeamRaleyghDamping(0.1);
    msection->SetDensity(2.400E-9);
    msection->SetSectionRotation(90*CH_C_DEG_TO_RAD);



    ChBuilderBeamEuler builder;
    if (elemFile.is_open()) {	
        ChVector<> pos;
        int elid;
        int node1, node2;       	
        unsigned int idelem=0;
        while (elemFile >> node1>> node2) { 
            std::cout<<idelem<<". element "<<node1<<" "<<node2<<std::endl; 
            auto nodeA = std::dynamic_pointer_cast<ChNodeFEAxyzrot>(my_mesh->GetNode(node1)); 		
            auto nodeB = std::dynamic_pointer_cast<ChNodeFEAxyzrot>(my_mesh->GetNode(node2)); 
                
            builder.BuildBeam(my_mesh,   // the mesh where to put the created nodes and elements
                    msection,  // the ChBeamSectionEulerAdvanced to use for the ChElementBeamEuler elements
                    1,         // the number of ChElementBeamEuler to create
                    nodeA,    // the 'A' point in space (beginning of beam)
                    nodeB,  // the 'B' point in space (end of beam)
                    ChVector<>(0, 0, 1));      // the 'Y' up direction of the section for the beam                		
        }
    }
    else{
        throw ChException("ERROR opening element info file: " + std::string(elemFilename) + "\n");
        exit(EXIT_FAILURE);
    }
    
    
    auto elnum=my_mesh->GetNelements();
    std::cout << "elnum " << elnum<<std::endl;
    
    
    for (int i=0; i<elnum; ++i){
        auto elem = std::dynamic_pointer_cast<ChElementBeamEuler>(my_mesh->GetElement(i));    	
        auto node1=elem->GetNodeA();
        auto node2=elem->GetNodeB();
        
        std::cout<<"element : "<< i <<" node1 : "<< node1->GetPos() <<" node2 : "<< node2->GetPos() << std::endl;
    }
            \n""")







        # Read the facets from file
        output_file.write("""       
    // Read the facets from the file facetsFilename
    // Supports 19 columns (no RF) or 22 columns (with E_rf str_rf frc_rf)
    std::vector<int> facet_tet, facet_IDx, facet_IDy, facet_IDz, facet_mF;
    std::vector<double> facet_Vol, facet_pArea;
    std::vector<double> facet_cx, facet_cy, facet_cz;
    std::vector<double> facet_px, facet_py, facet_pz;
    std::vector<double> facet_qx, facet_qy, facet_qz;
    std::vector<double> facet_sx, facet_sy, facet_sz;
    std::vector<double> facet_E_rf, facet_str_rf, facet_frc_rf;
    if (!facetsFile.is_open()) {
        std::cerr << \"ERROR: Could not open facets file\";
        return 0;
    }
    int Tet, IDx, IDy, IDz, mF;
    double Vol, pArea, cx, cy, cz, px, py, pz, qx, qy, qz, sx, sy, sz;
    double E_rf, str_rf, frc_rf;
    std::string line;
    while (std::getline(facetsFile, line)) {
        if (line.empty())
            continue;
        if (line.rfind(\"//\", 0) == 0)
            continue;
        std::istringstream iss(line);
        if (!(iss >> Tet >> IDx >> IDy >> IDz >> Vol >> pArea >> cx >> cy >> cz >> px >> py >> pz >> qx >> qy >> qz >> sx >> sy >> sz >> mF))
            continue;
        if (!(iss >> E_rf >> str_rf >> frc_rf)) {
            E_rf = 1.0;
            str_rf = 1.0;
            frc_rf = 1.0;
        }
        facet_tet.push_back(Tet);
        facet_IDx.push_back(IDx);
        facet_IDy.push_back(IDy);
        facet_IDz.push_back(IDz);
        facet_Vol.push_back(Vol);
        facet_pArea.push_back(pArea);
        facet_cx.push_back(cx);
        facet_cy.push_back(cy);
        facet_cz.push_back(cz);
        facet_px.push_back(px);
        facet_py.push_back(py);
        facet_pz.push_back(pz);
        facet_qx.push_back(qx);
        facet_qy.push_back(qy);
        facet_qz.push_back(qz);
        facet_sx.push_back(sx);
        facet_sy.push_back(sy);
        facet_sz.push_back(sz);
        facet_mF.push_back(mF);
        facet_E_rf.push_back(E_rf);
        facet_str_rf.push_back(str_rf);
        facet_frc_rf.push_back(frc_rf);
    }
    facetsFile.close();
    std::cout << \"Loaded \" << facet_tet.size() << \" facets (E_rf/str_rf/frc_rf available).\" << std::endl;

        \n""")
        output_file.write('    mesh->SetMaterialProperties(')

        for x in range(len(materialProps)):
            output_file.write(materialProps[x] + ', ')
        output_file.write(');\n')        




        ### Area to be fixed
        #analysis.Nodes = []
        #analysis.Elements = []
        #analysis.Materials = []


        # Get the mesh to solve
        mesh = membertools.get_mesh_to_solve(App.getDocument(App.ActiveDocument.Name).getObject(analysisName))        

        Nodes = []
        Elements = []
        Materials = []


        # Create the finite element mesh
        output_file.write("    // Create the finite element mesh\n")
        output_file.write("    std::map<int, std::shared_ptr<ChNodeFEAbase>> node_map;\n")
        for node in Nodes:
            output_file.write("    auto node_{} = std::make_shared<ChNodeFEAxyz>(ChVector<>({}, {}, {}));\n".format(node.Index, node.Point[0], node.Point[1], node.Point[2]))
            output_file.write("    node_{}->SetIndex({});\n".format(node.Index, node.Index))
            output_file.write("    mesh.AddNode(node_{});\n".format(node.Index))
            output_file.write("    node_map[{}] = node_{};\n".format(node.Index, node.Index))
        for element in Elements:
            output_file.write("    {\n")
            output_file.write("        std::vector<std::shared_ptr<ChNodeFEAbase>> element_nodes;\n")
            for node in element.Nodes:
                output_file.write("        element_nodes.push_back(node_map[{}]);\n".format(node.Index))
            output_file.write("        auto element_{} = std::make_shared<ChElementShellANCF>();\n".format(element.Index))
            output_file.write("        element_{}->SetNodes(element_nodes[0], element_nodes[1], element_nodes[2], element_nodes[3]);\n".format(element.Index))
            output_file.write("        mesh.AddElement(element_{});\n".format(element.Index))
            output_file.write("    }\n")
        output_file.write("\n")

        # Set the node positions and velocities
        output_file.write("    // Set the node positions and velocities\n")
        for node in Nodes:
            output_file.write("    {\n")
            output_file.write("        auto node_ptr = std::dynamic_pointer_cast<ChNodeFEAxyz>(node_map[{}]);\n".format(node.Index))
            output_file.write("        node_ptr->SetPos({0}, {1}, {2});\n".format(node.Point[0], node.Point[1], node.Point[2]))
            output_file.write("        node_ptr->SetPos_dt({0}, {1}, {2});\n".format(node.Velocity[0], node.Velocity[1], node.Velocity[2]))
            output_file.write("    }\n")
        output_file.write("\n")

        # Set the nodal forces and boundary conditions
        output_file.write("    // Set the nodal forces and boundary conditions\n")
        for node in Nodes:
            if node.Force is not None:
                output_file.write("    {\n")
                output_file.write("        auto node_ptr = std::dynamic_pointer_cast<ChNodeFEAxyz>(node_map[{}]);\n".format(node.Index))
                force_vec = node.Force
                output_file.write("        ChVector<> force_vec({0}, {1}, {2});\n".format(force_vec[0], force_vec[1], force_vec[2]))
                output_file.write("        node_ptr->SetForce(force_vec);\n")
                output_file.write("    }\n")
        output_file.write("\n")

        # Create a material composition and add the materials to it
        output_file.write("    // Create a material composition and add the materials to it\n")
        output_file.write("    auto composition = std::make_shared<ChMaterialShellANCF>();\n")
        for material in Materials:
            if isinstance(material, Fem.ElasticMaterial): # type: ignore
                output_file.write("    composition->AddLayer({}, {}, {});\n".format(material.Thickness, material.ElasticModulus, material.PoissonRatio))
            elif isinstance(material, Fem.InelasticLinearMaterial):# type: ignore
                output_file.write("    composition->AddLayer({}, {}, {}, {});\n".format(material.Thickness, material.ElasticModulus, material.PoissonRatio, material.YieldStress))
            elif isinstance(material, Fem.InelasticTensionCompressionMaterial):# type: ignore
                output_file.write("    composition->AddLayer({}, {}, {}, {}, {});\n".format(material.Thickness, material.ElasticModulus, material.PoissonRatio, material.YieldStress, material.CompressiveYieldStress))
            elif isinstance(material, Fem.InelasticKinematicHardeningMaterial):# type: ignore
                output_file.write("    composition->AddLayer({}, {}, {}, {}, {}, {});\n".format(material.Thickness, material.ElasticModulus, material.PoissonRatio, material.YieldStress, material.KinematicHardeningModulus, material.KinematicHardeningCoeff))
            elif isinstance(material, Fem.InelasticCombinedMaterial):# type: ignore
                output_file.write("    composition->AddLayer({}, {}, {}, {}, {}, {}, {}, {});\n".format(material.Thickness, material.ElasticModulus, material.PoissonRatio, material.YieldStress, material.CompressiveYieldStress, material.KinematicHardeningModulus, material.IsotropicHardeningModulus, material.KinematicHardeningCoeff))
        output_file.write("\n")


        # Set the material composition for all elements
        output_file.write("    // Set the material composition for all elements\n")
        for element in Elements:
            output_file.write("    {\n")
            output_file.write("        auto element_shell = std::dynamic_pointer_cast<ChElementShellANCF>(mesh.GetElement({}));\n".format(element.Index))
            output_file.write("        element_shell->AddLayer(composition);\n")
            output_file.write("    }\n")
        output_file.write("\n")




        output_file.write("""\n
    // Create a Chrono solver and set solver settings
    auto solver = chrono_types::make_shared<ChSolverMINRES>();
    sys.SetSolver(solver);
    sys.SetSolverType(ChSolver::Type::SPARSE_LU);
    solver->SetMaxIterations(500);
    solver->SetTolerance(1e-15);
    solver->EnableDiagonalPreconditioner(true);
    solver->EnableWarmStart(true);  // IMPORTANT for convergence when using EULER_IMPLICIT_LINEARIZED
    solver->SetVerbose(false);
    sys.SetSolverForceTolerance(1e-14);
    sys.SetTimestepperType(ChTimestepper::Type::EULER_IMPLICIT_PROJECTED);

    // Use the parallel processing capabilities of Chrono to run the simulation on multiple cores\n""") 
        output_file.write("    int num_threads = " + str(int(analysis.NumberOfThreads)) + ";\n")
        output_file.write("    ChOMPUtils::SetNumThreads(num_threads);\n")
        output_file.write("    system.SetParallelThreadNumber(num_threads);\n")
        output_file.write("    system.GetSettings()->max_threads = num_threads;\n\n")


        # Set up the time integration loop and output files for Paraview at set time increments
        output_file.write("    // Set up the time integration loop and output files for Paraview at set time increments\n")
        output_file.write("    double next_output_time = 0;\n")
        output_file.write("    double output_step = 0.1;\n")
        output_file.write("    for (double t = 0; t <= TotalTime; t += TimestepSize) {\n\n")

        # Output mesh data to a VTK file at set time increments
        output_file.write("        // Output mesh data to a VTK file at set time increments\n")
        output_file.write("        if (t == 0 || t >= next_output_time) {\n")
        output_file.write("            std::string filename = \"output_\" + std::to_string(int(t*100)) + \".vtk\";\n")
        output_file.write("            std::ofstream vtk_file(filename);\n")
        output_file.write("            vtk_file << \"# vtk DataFile Version 2.0\\n\";\n")
        output_file.write("            vtk_file << \"FEM Mesh Data\\n\";\n")
        output_file.write("            vtk_file << \"ASCII\\n\";\n")
        output_file.write("            vtk_file << \"DATASET UNSTRUCTURED_GRID\\n\";\n")
        output_file.write("            vtk_file << \"POINTS \" << mesh.GetNnodes() << \" double\\n\";\n")
        output_file.write("            for (const auto& node : mesh.GetNodes()) {\n")
        output_file.write("                vtk_file << node->GetPos().x() << \" \" << node->GetPos().y() << \" \" << node->GetPos().z() << \"\\n\";\n")
        output_file.write("            }\n")
        output_file.write("            vtk_file << \"CELLS \" << mesh.GetNelements() << \" \" << (4 * mesh.GetNelements()) << \"\\n\";\n")
        output_file.write("            for (const auto& element : mesh.GetElements()) {\n")
        output_file.write("                auto element_shell = std::dynamic_pointer_cast<ChElementShellANCF>(element);\n")
        output_file.write("                if (element_shell) {\n")
        output_file.write("                    vtk_file << \"4 \" << element_shell->GetNodeN(0)->GetIndex() << \" \" << element_shell->GetNodeN(1)->GetIndex() << \" \" << element_shell->GetNodeN(2)->GetIndex() << \" \" << element_shell->GetNodeN(3)->GetIndex() << \"\\n\";\n")
        output_file.write("        }\n")
        output_file.write("    }\n\n")

        # Output the final mesh state to a VTK file
        output_file.write("    // Output the final mesh state to a VTK file\n")
        output_file.write("    std::string filename = \"output_final.vtk\";\n")
        output_file.write("    std::ofstream vtk_file(filename);\n")
        output_file.write("    vtk_file << \"# vtk DataFile Version 2.0\\n\";\n")
        output_file.write("    vtk_file << \"FEM Mesh Data\\n\";\n")
        output_file.write("    vtk_file << \"ASCII\\n\";\n")
        output_file.write("    vtk_file << \"DATASET UNSTRUCTURED_GRID\\n\";\n")
        output_file.write("    vtk_file << \"POINTS \" << mesh.GetNnodes() << \" double\\n\";\n")
        output_file.write("    for (const auto& node : mesh.GetNodes()) {\n")
        output_file.write("        vtk_file << node->GetPos().x() << \" \" << node->GetPos().y() << \" \" << node->GetPos().z() << \"\\n\";\n")
        output_file.write("    }\n")
        output_file.write("    vtk_file << \"CELLS \" << mesh.GetNelements() << \" \" << (4 * mesh.GetNelements()) << \"\\n\";\n")
        output_file.write("    for (const auto& element : mesh.GetElements()) {\n")
        output_file.write("        auto element_shell = std::dynamic_pointer_cast<ChElementShellANCF>(element);\n")
        output_file.write("        if (element_shell) {\n")
        output_file.write("            vtk_file << \"4 \" << element_shell->GetNodeN(0)->GetIndex() << \" \" << element_shell->GetNodeN(1)->GetIndex() << \" \" << element_shell->GetNodeN(2)->GetIndex() << \" \" << element_shell->GetNodeN(3)->GetIndex() << \"\\n\";\n")
        output_file.write("        }\n")
        output_file.write("    }\n")
        output_file.write("    vtk_file << \"CELL_TYPES \" << mesh.GetNelements() << \"\\n\";\n")
        output_file.write("    for (const auto& element : mesh.GetElements()) {\n")
        output_file.write("        auto element_shell = std::dynamic_pointer_cast<ChElementShellANCF>(element);\n")
        output_file.write("        if (element_shell) {\n")
        output_file.write("            vtk_file << \"9\\n\";\n")
        output_file.write("        }\n")
        output_file.write("    }\n")
        output_file.write("    vtk_file << \"POINT_DATA \" << mesh.GetNnodes() << \"\\n\";\n")
        output_file.write("    vtk_file << \"SCALARS displacement double 3\\n\";\n")
        output_file.write("    vtk_file << \"LOOKUP_TABLE default\\n\";\n")
        output_file.write("    for (const auto& node : mesh.GetNodes()) {\n")
        output_file.write("        vtk_file << node->GetPos().x() - node->GetX0().x() << \" \" << node->GetPos().y() - node->GetX0().y() << \" \" << node->GetPos().z() - node->GetX0().z() << \"\\n\";\n")
        output_file.write("    }\n")
        output_file.write("}\n")