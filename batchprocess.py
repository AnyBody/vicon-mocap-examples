""" Script for batch processing all AnyBody-vicon examples .
   
   The script runs batch processing in three steps:

   1. Runs all the standing reference trials to 
      calculate scaling and marker positions for each subject. 

   2. Runs marker tracking for all trials, saving joint angles to files. 

   3. It runs the inverse dyanmic analysis for all trials.
      This steps outputs the EKin variable. But can be extended
      to output any variable from the model. 

   Note: The script uses AnyPyTools, which is an open source library for 
         working with the AnyBody Modeling System. If you use this library 
         for publication please cite:

         Lund et al., (2019). AnyPyTools: A Python package for reproducible 
         research with the AnyBody Modeling System. Journal of Open Source 
         Software, 4(33), 1108, https://doi.org/10.21105/joss.01108

"""
#%%
import os

try: 
    import anypytools
    import anypytools.macro_commands as mc
except ImportError as e:
    raise ImportError(
        "AnyPyTools missing. Please install the AnyPyTools library to run batch processing: "
        "https://anybody-research-group.github.io/anypytools-docs/"
    )


# Create folder for storing batch processing logfiles
# note: log files are automatically deleted unless the model fails.
os.makedirs("BatchProcessingLogs", exist_ok=True)
os.makedirs("VideoOutput", exist_ok=True)


# List of search strings to find trials from the different 
# activities in the vicon dataset
# Some entries are present multiple times due to inconsisting naming 
# in the Vicon dataset.
trials = [
    "BaseBall_\d+", #Baseball
    "ThrowDown_\d+", #Cricket
    "Trial\d+", #Cycling
    "Walking \d+", # Walking (Gait/Kory)
    "Walking\d+", # Walking (Gait/Mike)
    "Swing\d+", #Golf
    "Running_\d\d", # Threadmill running
    "RunningCluster_\d\d", # Threadmill running
    "Capture\d\d\d", # Table tennis
]


#%% Process all standing reference trials

macro = [
    mc.Load("Main.any"),
    mc.OperationRun("Main.RunParameterIdentification"),
]

app = anypytools.AnyPyProcess(num_processes=6)
print("Starting parameter optimizaiton (anthropometrics, marker positions)")
results = app.start_macro(
    macro,
    search_subdirs=rf"(Static|Cal 01|Calibration)[\\/]Main.any",
    logfile="BatchProcessingLogs/ParameterOptimization.txt",
)


#%% Process all bicycle reference trials
macro = [
    mc.Load("Main.any"),
    mc.OperationRun("Main.RunParameterIdentification_External"),
]

app = anypytools.AnyPyProcess(num_processes=6)
print("Starting parameter optimizaiton of External equipment (bat, club, bike etc.)")
results = app.start_macro(
    macro,
    search_subdirs=rf".*(_Fit.+)[\\/]Main.any",
    logfile="BatchProcessingLogs/ExternalObjectParameterOptimization.txt",
)

#%% Process all marker tracking

macro = [
    mc.Load("Main.any"),
    mc.OperationRun("Main.RunAnalysis.LoadParameters"),
    mc.OperationRun("Main.RunAnalysis.MarkerTracking"),
]

app = anypytools.AnyPyProcess(num_processes=6, ignore_errors=[".anyset"])
print("Starting Marker tracking")
results = app.start_macro(
    macro,
    search_subdirs=rf"({'|'.join(trials)})[\\/]Main.any",
    logfile="BatchProcessingLogs/MarkerTracking.txt",
)

#%% Process all Inverse dynamics and export results


macro = [
    mc.Load("Main.any"),
    mc.OperationRun("Main.RunAnalysis.LoadParameters"),
    mc.OperationRun("Main.Studies.InverseDynamicStudy.VideoTool.Create_Video.Reset"),
    mc.OperationRun("Main.Studies.InverseDynamicStudy.VideoTool.Create_Video.StartTrigger"),
    mc.OperationRun("Main.RunAnalysis.InverseDynamics"),
    mc.OperationRun("Main.Studies.InverseDynamicStudy.VideoTool.Create_Video.StopTrigger"),
    mc.OperationRun("Main.Studies.InverseDynamicStudy.VideoTool.Create_Video.ConvertVideo"),
    mc.OperationRun("Main.Studies.InverseDynamicStudy.VideoTool.Create_Video.RemoveImageFiles"),
    # Add more output here
]

app = anypytools.AnyPyProcess(num_processes=4, ignore_errors=[".anyset"])
results = app.start_macro(
    macro,
    search_subdirs=rf"({'|'.join(trials)})[\\/]Main.any",
    logfile="BatchProcessingLogs/InverseDynamics.txt",
)

# Please see
# https://anybody-research-group.github.io/anypytools-docs/Tutorial/01_Getting_started_with_anypytools.html
# for how to work with the results from AnyPyTools
