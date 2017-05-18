droplet_script_template = """
# Start "User Interface" 
############################ 
Name_of_Simulation = 'Test'
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
"""