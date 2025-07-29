"""
urdf_visualizer.py
===================

Utilities for loading a URDF file and computing the Cartesian
transformations of each link given a set of joint positions.  This
module leverages the `urdfpy` library, which provides a convenient
Python API for parsing URDF/Xacro models and performing forward
kinematics.  It is separated from the Streamlit UI so that other
visualisation frameworks can reuse the same logic.

Functions
---------

* :func:`load_robot`: Load a URDF from a file on disk and return a
  `urdfpy.URDF` object.  If the input is a `.xacro` file, it will be
  processed via the `xacro` command before loading.  The user must
  ensure that `xacro` is installed and available in the PATH.
* :func:`compute_link_frames`: Given a URDF and joint positions,
  compute the homogeneous transform of each link relative to the base
  frame.  Returns a dictionary mapping link names to 4×4
  transformation matrices (numpy arrays).

Example usage
-------------

>>> from urdf_visualizer import load_robot, compute_link_frames
>>> robot = load_robot('path/to/crb15000_5_95.xacro')
>>> joint_positions = {'joint_1': 0.0, 'joint_2': 0.1, ...}
>>> frames = compute_link_frames(robot, joint_positions)
>>> # frames['tool0'] is the 4×4 transform of the end effector

Dependencies
------------

* `urdfpy`: install via ``pip install urdfpy``
* `xacro`: for processing `.xacro` files.  This is typically part of
  the ROS 2 package `ros-foxy-xacro` or similar.  On Ubuntu, install
  via ``sudo apt install ros-${ROS_DISTRO}-xacro``.
"""

import os
import collections
import collections.abc
import subprocess
import tempfile
from typing import Dict, Tuple

import numpy as np

# -----------------------------------------------------------------------------
# Compatibility workaround for deprecated NumPy scalar aliases.
#
# NumPy 1.20 removed ``np.float`` and other scalar type aliases in favour of
# the builtin types.  Some third-party packages (e.g. older urdfpy or
# trimesh) may still reference these names, resulting in an ``AttributeError``.
# To maintain compatibility across NumPy versions, define these aliases if
# they're missing.  Using the builtin types preserves behaviour and is safe.
for _alias, _type in [('float', float), ('int', int), ('bool', bool)]:
    if not hasattr(np, _alias):
        setattr(np, _alias, _type)

# -----------------------------------------------------------------------------
# Compatibility workaround for deprecated NumPy scalars
#
# NumPy 1.20 removed aliases like ``np.float`` and ``np.int`` in favour of
# the builtin types.  Some dependencies (e.g. older versions of urdfpy or
# trimesh) may still reference these names, causing AttributeError.  To
# maintain compatibility across NumPy versions, define the aliases if they
# don't already exist.  This is safe because ``float`` and ``int`` behave
# identically for our purposes.
for _alias, _type in [('float', float), ('int', int), ('bool', bool)]:
    if not hasattr(np, _alias):
        setattr(np, _alias, _type)
"""
Work around Python 3.12 removal of collections.Mapping.

NetworkX (a dependency of urdfpy) imports ``Mapping`` from the
``collections`` module.  In Python 3.10 and earlier this was valid,
but from Python 3.11 onwards the abstract base classes were moved to
``collections.abc`` and removed from ``collections``.  To maintain
compatibility until networkx releases a fix, we alias the missing
attributes from ``collections.abc``【955574263095724†L30-L67】.
"""
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping  # type: ignore
if not hasattr(collections, 'MutableMapping'):
    collections.MutableMapping = collections.abc.MutableMapping  # type: ignore
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence  # type: ignore

from urdfpy import URDF


def load_robot(urdf_path: str) -> URDF:
    """Load a robot description from a URDF or Xacro file.

    Parameters
    ----------
    urdf_path : str
        Path to the URDF or Xacro file.  If the suffix is `.xacro`, the
        file will be processed with the `xacro` command first.

    Returns
    -------
    URDF
        Parsed URDF model ready for kinematic computations.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    RuntimeError
        If the `xacro` processing fails.
    """
    if not os.path.exists(urdf_path):
        raise FileNotFoundError(f'{urdf_path} does not exist')

    # Helper function to perform package URI replacement and, when necessary,
    # strip out visual and collision elements to avoid mesh dependencies.  The
    # `urdfpy` API changed across versions: recent releases provide
    # ``URDF.from_xml_string`` and a ``load_meshes`` argument, while older
    # versions only support ``URDF.load()``.  To maintain compatibility,
    # construct the XML string manually and branch based on available
    # methods.  When falling back to ``URDF.load()``, we remove the
    # ``<visual>`` and ``<collision>`` sections entirely so that missing mesh
    # files do not cause errors.
    def _parse_xml(xml_str: str) -> URDF:
        """Parse a URDF XML string into a URDF object, adapting to
        available urdfpy API.  Replaces package URIs and optionally strips
        mesh references."""
        # Attempt to resolve the ABB package to an absolute directory.
        try:
            from ament_index_python.packages import get_package_share_directory
            share_dir = get_package_share_directory('abb_crb15000_support')
            xml_str = xml_str.replace('package://abb_crb15000_support', share_dir)
            # Only print success message for package resolution
        except Exception as e:
            # If the package can't be found, leave the URI unchanged.  The
            # user may still mount the meshes into the expected location.
            pass
        # Prefer the newer API if available.
        if hasattr(URDF, 'from_xml_string'):
            try:
                # Some versions support a 'load_meshes' argument.  Use it
                # conditionally.
                import inspect
                if 'load_meshes' in inspect.signature(URDF.from_xml_string).parameters:
                    return URDF.from_xml_string(xml_str, load_meshes=True)
                else:
                    return URDF.from_xml_string(xml_str)
            except Exception as e:
                # Fall back to file-based loading if parsing fails.
                pass
        
        # Try loading with meshes using temporary file approach
        try:
            with tempfile.NamedTemporaryFile(suffix='.urdf', delete=False) as tmp_file:
                tmp_file.write(xml_str.encode('utf-8'))
                tmp_path = tmp_file.name
            try:
                robot = URDF.load(tmp_path)
                return robot
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            # Only as last resort: remove visual/collision tags to avoid mesh loading errors
            import re
            # Remove visual and collision blocks entirely.
            stripped_xml = re.sub(r'<visual>(.*?)</visual>', '', xml_str, flags=re.DOTALL)
            stripped_xml = re.sub(r'<collision>(.*?)</collision>', '', stripped_xml, flags=re.DOTALL)
            with tempfile.NamedTemporaryFile(suffix='.urdf', delete=False) as tmp_file:
                tmp_file.write(stripped_xml.encode('utf-8'))
                tmp_path = tmp_file.name
            try:
                return URDF.load(tmp_path)
            finally:
                os.unlink(tmp_path)

    # If the input is a Xacro file, expand it to URDF via the xacro CLI.
    if urdf_path.endswith('.xacro'):
        with tempfile.NamedTemporaryFile(suffix='.urdf', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            # Run xacro to produce a URDF.  This may throw if xacro is
            # unavailable or the file cannot be processed.
            subprocess.run(['xacro', urdf_path, '-o', tmp_path], check=True)
            with open(tmp_path, 'r') as f:
                xml = f.read()
            robot = _parse_xml(xml)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f'Failed to run xacro on {urdf_path}: {exc}')
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        # For plain URDF files, read the XML and parse it.
        with open(urdf_path, 'r') as f:
            xml = f.read()
        robot = _parse_xml(xml)
    return robot


def compute_link_frames(robot: URDF, joint_positions: Dict[str, float]) -> Dict[str, np.ndarray]:
    """Compute the homogeneous transform of each link given joint positions.

    Parameters
    ----------
    robot : URDF
        The parsed URDF model.
    joint_positions : Dict[str, float]
        Mapping from joint name to position in radians.

    Returns
    -------
    Dict[str, numpy.ndarray]
        Dictionary mapping link names to 4×4 transformation matrices.  If a
        joint name is not provided in ``joint_positions``, its default
        value (usually 0) is assumed.
    """
    # Prepare configuration for urdfpy - handle both list and dict formats
    # depending on the urdfpy version
    try:
        # Try the newer API that accepts a configuration dictionary
        cfg = {}
        for joint in robot.joints:
            if joint.joint_type != 'fixed':
                cfg[joint.name] = joint_positions.get(joint.name, 0.0)
        frames = robot.link_fk(cfg=cfg)
    except (TypeError, AttributeError):
        # Fall back to the older API that expects a list
        q = []
        for joint in robot.joints:
            if joint.joint_type == 'fixed':
                continue
            q.append(joint_positions.get(joint.name, 0.0))
        frames = robot.link_fk(q)
    
    # Convert Link objects to string keys for consistent access
    string_frames = {}
    for link_key, transform in frames.items():
        if hasattr(link_key, 'name'):
            # Link object - use its name
            string_frames[link_key.name] = transform
        else:
            # Already a string
            string_frames[str(link_key)] = transform
    
    return string_frames
