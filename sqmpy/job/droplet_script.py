droplet_script_template = """
activate_this = '/home/has/simphony/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Example to solve 3D 1-phase poiseuille flow

from simphony.core.cuba import CUBA

from simphony.api import CUDS, Simulation
from simphony.cuds.meta import api
from simphony.engine import EngineInterface

import tempfile

import numpy as np
import math
import foam_controlwrapper
# Start "User Interface" 
############################ 
Name_of_Simulation = '{simulation_name}'
# Note: Please Use SI units (Kg, metre, second) 

# Simulation Set Up Section 
#-------------------------- 
Simulation_Box_Side_Length = {simulation_box_side_length}    # meters 
Mesh_Grid_Size = {mesh_grid_size}
 
 
# Time Section  
#-------------------------- 
End_Time = {end_time}
Time_Step = {time_step}
Number_of_States = {number_of_states}
 
# Material Properties Section 
#-------------------------- 
Wetting_Angle = {wetting_angle}
Drop_Volume = {drop_volume}
Dynamic_Viscosity_of_Gas_Phase = {dynamic_viscosity_of_gas_phase}
Density_of_Gas_Phase = {density_of_gas_phase}
Dynamic_Viscosity_of_Liquid_Phase = {dynamic_viscosity_of_liquid_phase}
Density_of_Liquid_Phase = {density_of_liquid_phase}
Surface_Tension_of_Liquid_Gas_Interface = {surface_tension_of_liquid_gas_interface}
 
# End "User Interface" 
# After this point, the script should run in  
# the "background", no additional visualisation 
# is needed! 
############################ 
name = 'droplet'
mesh_name = 'droplet_mesh'

# create cuds
cuds = CUDS(name=name)

boxlen = Simulation_Box_Side_Length
grid_size = Mesh_Grid_Size 

end_time = End_Time
timestep = Time_Step

drop_vol = Drop_Volume
wetang_wall = Wetting_Angle # moderate hydrophobic

dyn_visc_gas = Dynamic_Viscosity_of_Gas_Phase # 1.48e-5 # air
dens_gas = Density_of_Gas_Phase # 1.0  # air

dyn_visc_liq = Dynamic_Viscosity_of_Liquid_Phase # 0.002 # wt%25 glycerol/water
dens_liq = Density_of_Liquid_Phase # 1058.0 # wt%25 glycerol/water
surftens = Surface_Tension_of_Liquid_Gas_Interface # 70.0e-3 # wt%25 glycerol/water - air

# physics model
cfd = api.Cfd(name='default model')
# add to cuds
cuds.add([cfd])

# materials
liquid = api.Material(name='liquid')
liquid.data[CUBA.DENSITY] = dens_liq
liquid.data[CUBA.DYNAMIC_VISCOSITY] = dyn_visc_liq
cuds.add([liquid])

gas = api.Material(name='gas')
gas.data[CUBA.DENSITY] = dens_gas
gas.data[CUBA.DYNAMIC_VISCOSITY] = dyn_visc_gas
cuds.add([gas])


# surface tension
st = api.SurfaceTensionRelation(material=[liquid, gas],
                                surface_tension=surftens)
cuds.add([st])

# free surface model

fsm = api.FreeSurfaceModel(name='vof')
cuds.add([fsm])

# time setting
sim_time = api.IntegrationTime(name='simulation_time',
                               current=0.0,
                               final=end_time,
                               size=timestep)
cuds.add([sim_time])

# solver parameters
sp = api.SolverParameter(name='solver_parameters')
sp.data[CUBA.MAXIMUM_COURANT_NUMBER] = 0.2
sp.data[CUBA.NUMBER_OF_PHYSICS_STATES] = Number_of_States

gm = api.GravityModel(name='gravitation')
gm.acceleration = (0, -9.81, 0)
cuds.add([gm])

# boundary conditions
vel_inlet = api.InletOutletVelocity((0, 0, 0), liquid, name='vel_inlet')
vel_inlet.data[CUBA.VARIABLE] = CUBA.VELOCITY

pres_inlet = api.TotalPressureCondition(0.0, liquid, name='pres_inlet')
pres_inlet.data[CUBA.VARIABLE] = CUBA.DYNAMIC_PRESSURE

vf_inlet = api.InletOutletVolumeFraction(0.0, liquid, name='vf_inlet')
vf_inlet.data[CUBA.VARIABLE] = CUBA.VOLUME_FRACTION

vel_outlet = api.EmptyCondition(name='vel_outlet')
vel_outlet.data[CUBA.VARIABLE] = CUBA.VELOCITY

pres_outlet = api.EmptyCondition(name='pres_outlet')
pres_outlet.data[CUBA.VARIABLE] = CUBA.DYNAMIC_PRESSURE

vf_outlet = api.EmptyCondition(name='vf_outlet')
vf_outlet.data[CUBA.VARIABLE] = CUBA.VOLUME_FRACTION

vel_walls = api.ConstantVelocityCondition((0, 0, 0), liquid, name='vel_walls')

pres_walls = api.Neumann(liquid, name='pres_walls')
pres_walls.data[CUBA.VARIABLE] = CUBA.DYNAMIC_PRESSURE

vf_walls = api.WettingAngle([liquid, gas], contact_angle=wetang_wall,
                            name='vf_walls')
vf_walls.data[CUBA.VARIABLE] = CUBA.VOLUME_FRACTION

vel_frontAndBack = api.EmptyCondition(name='vel_frontAndBack')
vel_frontAndBack.data[CUBA.VARIABLE] = CUBA.VELOCITY

pres_frontAndBack = api.EmptyCondition(name='pres_frontAndBack')
pres_frontAndBack.data[CUBA.VARIABLE] = CUBA.DYNAMIC_PRESSURE

vf_frontAndBack = api.EmptyCondition(name='vf_frontAndBack')
vf_frontAndBack.data[CUBA.VARIABLE] = CUBA.VOLUME_FRACTION

# boundaries
inlet = api.Boundary(name='inlet', condition=[vel_inlet, pres_inlet, vf_inlet])
walls = api.Boundary(name='walls', condition=[vel_walls, pres_walls, vf_walls])
outlet = api.Boundary(name='outlet', condition=[vel_outlet, pres_outlet,
                                                vf_outlet])
frontAndBack = api.Boundary(name='frontAndBack', condition=[vel_frontAndBack,
                                                            pres_frontAndBack,
                                                            vf_frontAndBack])

cuds.add([inlet, walls, outlet, frontAndBack])


drop_len = 2.0 * (3.0/4.0 * math.pi * drop_vol)**(1./3.)
grid_size = min(drop_len/8.,grid_size)
num_grid = int(boxlen/grid_size)
grid_size = boxlen/float(num_grid)

print grid_size, num_grid

tmp_dir = tempfile.mkdtemp()
corner_points = [(0.0, 0.0, 0.0), (boxlen, 0.0, 0.0),
                 (boxlen, boxlen, 0.0), (0.0, boxlen, 0.0),
                 (0.0, 0.0, boxlen), (boxlen, 0.0, boxlen),
                 (boxlen, boxlen, boxlen), (0.0, boxlen, boxlen)]

mesh = foam_controlwrapper.create_quad_mesh(tmp_dir, mesh_name,
                                            corner_points, num_grid, num_grid,
                                            num_grid)
cuds.add([mesh])

mesh_in_cuds = cuds.get_by_name(mesh_name)

# initial state. In VOF only one velocity and pressure field

drop_cells = []  
zero_liquid = api.PhaseVolumeFraction(liquid, 0)
zero_gas = api.PhaseVolumeFraction(gas, 0)
one_liquid = api.PhaseVolumeFraction(liquid, 1)
one_gas = api.PhaseVolumeFraction(gas, 1)

for cell in mesh_in_cuds.iter(item_type=CUBA.CELL):
 
    xmid = sum(mesh_in_cuds._get_point(puid).coordinates[0]
               for puid in cell.points)
    xmid /= sum(1.0 for _ in cell.points)
    
    ymid = sum(mesh_in_cuds._get_point(puid).coordinates[1]
               for puid in cell.points)
    ymid /= sum(1.0 for _ in cell.points)
    
    zmid = sum(mesh_in_cuds._get_point(puid).coordinates[2]
               for puid in cell.points)
    zmid /= sum(1.0 for _ in cell.points)
    
    if (xmid-boxlen/2.0)**2 + (ymid-boxlen/2.0)**2 + (zmid-boxlen/2.0)**2 > (drop_len/2.0)**2: # and abs(ymid-0.0005) < 0.0004 : # 0.12 = len_x, 0.006 = len_y
        cell.data[CUBA.VOLUME_FRACTION] = [zero_liquid, one_gas]
    else:
        cell.data[CUBA.VOLUME_FRACTION] = [one_liquid, zero_gas]

    cell.data[CUBA.DYNAMIC_PRESSURE] = 0.0
    cell.data[CUBA.VELOCITY] = [0.0, 0.0, 0.0]

    drop_cells.append(cell)

mesh_in_cuds._update_cells(drop_cells)

print "run simulation equilibrium"
sim = Simulation(cuds, 'OpenFOAM', engine_interface=EngineInterface.FileIO)

mesh_in_engine = cuds.get_by_name(mesh_name)
print "Case directory ", mesh_in_engine.path

sim.run()

import subprocess
subprocess.call(["tar", "-zcvf ", "results.tar.gz", mesh_in_engine.path])
import time
time.sleep(1000)
"""