"""
A class which takes care of a Full-Waveform Inversion using multiple meshes.
It uses Salvus, Lasif and Multimesh to perform most of its actions.
This is a class which wraps the three packages together to perform an
automatic Full-Waveform Inversion
"""
import numpy as np
import pyasdf
import lasif.api as lapi
import multi_mesh.api as mapi
from communicators import lasif, salvus_flow, salvus_opt
from storyteller import Storyteller


class autoinverter(object):
    """
    Ok lets do this.
    We need something that reads Salvus opt
    Something that talks to salvus flow
    Something that creates meshes
    Something that talks to lasif
    Something that talks to multimesh
    Something interacting with dp-s random selection (No need now)
    Something talking to the smoother.
    So let's create a few files:
    salvus_opt communicator
    salvus_flow communicator
    salvus_mesher (not necessary now)
    lasif communicator
    multimesh communicator
    I can regularly save the inversion_dict as a toml file and reload it
    """

    def __init__(self, info_dict: dict, simulation_dict: dict, inversion_dict: dict):
        self.info = info_dict
        self.sim_info = simulation_dict
        self.inversion_status = inversion_dict
        self.lasif = lasif.lasif_comm(self.info)
        self.salvus_flow = salvus_flow.salvus_flow_comm(
            self.info, self.sim_info)
        self.salvus_opt = salvus_opt.salvus_opt_comm(self.info)
        self.storyteller = Storyteller()

    def validate_inversion_project(self):
        """
        Make sure everything is correctly set up in order to perform inversion.

        :param info_dict: Information needed
        :type info_dict: dict
        :param simulation_dict: Information regarding simulations
        :type simulation_dict: dict
        """
        import pathlib

        if "inversion_name" not in self.info.keys():
            raise ValueError(
                "The inversion needs a name")

        # Salvus Opt
        if "salvus_opt_dir" not in self.info.keys():
            raise ValueError(
                "Information on salvus_opt_dir is missing from information")
        else:
            folder = pathlib.Path(self.info["salvus_opt_dir"])
            if not (folder / "inversion.toml").exists():
                raise ValueError("Salvus opt inversion not initiated")

        # Lasif
        if "lasif_project" not in self.info.keys():
            raise ValueError(
                "Information on lasif_project is missing from information")
        else:
            folder = pathlib.Path(self.info["lasif_project"])
            if not (folder / "lasif_config.toml").exists():
                raise ValueError("Lasif project not initialized")

        # Simulation parameters:
        if "end_time_in_seconds" not in self.sim_info.keys():
            raise ValueError(
                "Information regarding end time of simulation missing")

        if "time_step_in_seconds" not in self.sim_info.keys():
            raise ValueError(
                "Information regarding time step of simulation missing")

        if "start_time_in_seconds" not in self.sim_info.keys():
            raise ValueError(
                "Information regarding start time of simulation missing")

    def initialize_inversion(self):
        """
        Set up everything regarding the inversion. Make sure everything
        is correct and that information is there.
        Make this check status of salvus opt, the inversion does not have
        to be new to call this method.
        """
        # Will do later.

    def prepare_iteration(self):
        """
        Prepare iteration.
        Get iteration name from salvus opt
        Modify name in inversion status
        Create iteration
        Pick events
        Make meshes if needed
        """

    def interpolate_model(self, event: str, iteration: str):
        """
        Interpolate model to a simulation mesh

        :param event: Name of event
        :type event: str
        :param iteration: Name of iteration
        :type iteration: str
        """

    def interpolate_gradient(self, event: str, iteration: str):
        """
        Interpolate gradient to master mesh

        :param event: Name of event
        :type event: str
        :param iteration: Name of iteration
        :type iteration: str
        """

    def run_forward_simulation(self):
        """
        Submit forward simulation to daint and possibly monitor aswell
        """

    def run_adjoint_simulation(self):
        """
        Submit adjoint simulation to daint and possibly monitor
        """

    def misfit_quantification(self, adjoint: bool):
        """
        Compute misfit (and adjoint source) for iteration

        :param adjoint: Compute adjoint source?
        :type adjoint: bool
        """

    def perform_task(self, task: str):
        """
        Input a task and send to correct function

        :param task: task issued by salvus opt
        :type task: str
        """
        if task == "compute_misfit_and_gradient":
            self.prepare_iteration()
            # Figure out a way to do this on a per event basis.
            self.interpolate_model(
                event, self.inversion_status["iteration_name"])
            self.run_forward_simulation()
            self.misfit_quantification(adjoint=True)
            self.run_adjoint_simulation()
            self.storyteller.document_task(task)
            self.salvus_opt.close_salvus_opt_task()
            task = self.salvus_opt.read_salvus_opt()
            self.perform_task(task)

        elif task == "compute_misfit":
            self.prepare_iteration()
            self.run_forward_simulation()
            self.misfit_quantification(adjoint=True)
            self.salvus_opt.close_salvus_opt_task()
            task = self.salvus_opt.read_salvus_opt()
            self.perform_task(task)

        elif task == "compute_gradient":
            self.run_adjoint_simulation()
            # Cut sources and receivers?
            self.interpolate_gradient()
            # Smooth gradients
            self.salvus_opt.move_gradient_to_salvus_opt_folder(
                self.inversion_status["iteration_name"], event
            )
            self.salvus_opt.close_salvus_opt_task()
            task = self.salvus_opt.read_salvus_opt()
            self.perform_task(task)

        elif task == "finalize_iteration":
            self.salvus_opt.close_salvus_opt_task()
            task = self.salvus_opt.read_salvus_opt()
            self.perform_task(task)
            # Possibly delete wavefields

        else:
            raise ValueError(f"Salvus Opt task {task} not known")

    def run_inversion(self):
        """
        This is where the inversion runs.
        1. Check status of inversion
        2. Continue inversion

        Make iteration, select events for it.
        See whether events have meshes
        If not, make meshes

        Interpolate model to meshes
        as soon as an individual interpolation is done, submit job.

        If event not in control group, select windows.
        Retrieve results, calculate adjoint sources, submit adjoint jobs.

        Retrieve gradients, interpolate back, smooth.

        Update Model.

        Workflow:
                Read Salvus opt,
                Perform task,
                Document it
                Close task, repeat.
        """
        # Always do this as a first thing, Might write a different function for checking status
        self.initialize_inversion()

        task = self.salvus_opt.read_salvus_opt()

        self.perform_task(task)
