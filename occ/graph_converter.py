# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:30:39 2019

@author: 2624224
"""
import os
import glob
from multiprocessing import Pool
import logging
import pickle
import numpy as np
import argparse
import os.path as osp
import traceback
import sys

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.StepRepr import StepRepr_RepresentationItem
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.TopoDS import topods
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCC.Core.TopTools import TopTools_IndexedMapOfShape
from OCC.Core.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.Core.TopExp import topexp_MapShapesAndAncestors
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties, brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepTools import breptools_UVBounds, breptools
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomLProp import GeomLProp_SLProps

def feature_from_face(face_util):
    face = face_util
    gprops = GProp_GProps()
    if hasattr(brepgprop, 'SurfaceProperties'):
        brepgprop.SurfaceProperties(face, gprops)
    else:
        brepgprop_SurfaceProperties(face, gprops)
    pnt = gprops.CentreOfMass()
    if hasattr(breptools, 'UVBounds'):
        umin, umax, vmin, vmax = breptools.UVBounds(face)
    else:
        umin, umax, vmin, vmax = breptools_UVBounds(face)
    u = 0.5 * (umin + umax)
    v = 0.5 * (vmin + vmax)
    surf = BRepAdaptor_Surface(face, True)
    props = GeomLProp_SLProps(surf.Surface().Surface(), u, v, 1, 1e-6)
    normal_dir = props.Normal()
    normal = [normal_dir.X(), normal_dir.Y(), normal_dir.Z()]
    p = [pnt.X(), pnt.Y(), pnt.Z()]
    d = float(np.dot(normal, p))
    return normal + [d]


def list_faces(shape):
    faces = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        faces.append(topods.Face(exp.Current()))
        exp.Next()
    return faces


def shape_with_fid_from_step(filename):
    if not os.path.exists(filename):
        logging.info(filename + ' does not exist')
        return None, None

    reader = STEPControl_Reader()
    reader.ReadFile(filename)
    reader.TransferRoots()
    shape = reader.OneShape()

    treader = reader.WS().TransferReader()
    id_map = {}
    for face in list_faces(shape):
        item = treader.EntityFromShapeResult(face, 1)
        if item is None:
            continue
        item = StepRepr_RepresentationItem.DownCast(item)
        name = item.Name().ToCString()
        if not name:
            continue
        try:
            id_map[face] = int(name)
        except ValueError:
            continue
    return shape, id_map


def build_face_adjacency(shape):
    edge_to_faces = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp_MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edge_to_faces)
    return edge_to_faces


def graph_from_shape(a_shape):        
    a_graph = {}
    a_graph['y'] = a_shape['y']
    a_graph['x'] = [None] * len(a_shape['y'])
    a_graph['edge_index'] = [[],[]]

    edge_to_faces = a_shape['edge_to_faces']
    face_map = a_shape['face_map']

    for i in range(1, face_map.Size() + 1):
        face = topods.Face(face_map.FindKey(i))
        src_idx = i - 1
        a_graph['x'][src_idx] = feature_from_face(face)
        exp = TopExp_Explorer(face, TopAbs_EDGE)
        while exp.More():
            edge = exp.Current()
            exp.Next()
            if not edge_to_faces.Contains(edge):
                continue
            flist = edge_to_faces.FindFromKey(edge)
            if flist.Size() < 2:
                continue
            it = TopTools_ListIteratorOfListOfShape(flist)
            while it.More():
                other = topods.Face(it.Value())
                it.Next()
                if other.IsSame(face):
                    continue
                dst_i = face_map.FindIndex(other)
                if dst_i <= 0:
                    continue
                a_graph['edge_index'][0].append(src_idx)
                a_graph['edge_index'][1].append(dst_i - 1)
    return a_graph 


def save_graph(graph, graph_path, shape_name):
    with open(os.path.join(graph_path, shape_name + '.graph'), 'wb') as file:
        pickle.dump(graph, file)

    
def generate_graph(arg):
    '''
    generate points for shapes listed in CATEGORY_NAME_step.txt
    '''
    shape_dir = arg[0]
    graph_path = arg[1]
    shape_name = arg[2]

#    logging.info(shape_name)
    if os.path.exists(os.path.join(graph_path, shape_name + '.graph')):
        return 0
    try:
        step_path = os.path.join(shape_dir, shape_name + '.step')
        shape_obj, fid_map = shape_with_fid_from_step(step_path)
        if shape_obj is None or fid_map is None or len(fid_map) == 0:
            logging.info(shape_name + ' failed loading')
            return -1

        label_path = os.path.join(shape_dir, shape_name + '.face_truth')
        with open(label_path, 'rb') as file:
            face_labels = pickle.load(file)

        face_map = TopTools_IndexedMapOfShape()
        exp = TopExp_Explorer(shape_obj, TopAbs_FACE)
        while exp.More():
            face_map.Add(exp.Current())
            exp.Next()

        y = [None] * face_map.Size()
        for face in fid_map:
            idx = face_map.FindIndex(face)
            if idx <= 0:
                continue
            name_id = fid_map[face]
            y[idx - 1] = face_labels[name_id]

        if any(v is None for v in y):
            logging.info(shape_name + ' has unmapped faces/labels')
            return -1

        a_shape = {
            'shape': shape_obj,
            'face_ids': fid_map,
            'y': y,
            'face_map': face_map,
            'edge_to_faces': build_face_adjacency(shape_obj),
        }
    except Exception:
        logging.info(shape_name + ' failed loading')
        logging.info(traceback.format_exc())
        return -1

    try:
        a_graph = graph_from_shape(a_shape)
    except Exception:
        logging.info(shape_name + 'failed to create graph')
        logging.info(traceback.format_exc())
        return -1

    save_graph(a_graph, graph_path, shape_name)
    return 1


parser = argparse.ArgumentParser()
parser.add_argument('--shape_dir', 
                    default=osp.abspath(osp.join(osp.dirname(osp.realpath(__file__)), '../dataset/step/')) + os.sep, 
                    help="Directory containing the step files")
parser.add_argument('--graph_dir', 
                    default=osp.abspath(osp.join(osp.dirname(osp.realpath(__file__)), '../dataset/graph/')), 
                    help="Directory containing the step files")
parser.add_argument('--max_shapes', type=int, default=0,
                    help="Convert at most this many shapes (0 = all)")
parser.add_argument('--workers', type=int, default=0,
                    help="Number of worker processes (0 = use multiprocessing default; 1 = run sequentially)")
args = parser.parse_args()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(processName)s:%(message)s',
        handlers=[
            logging.FileHandler(osp.join(osp.dirname(osp.realpath(__file__)), 'graph_converter.log'), mode='a'),
            logging.StreamHandler(sys.stdout),
        ],
    )

    if not os.path.exists(args.graph_dir):
        os.makedirs(args.graph_dir, exist_ok=True)
    
    shape_paths = glob.glob(osp.join(args.shape_dir, '*.step'))
    if args.max_shapes and args.max_shapes > 0:
        shape_paths = shape_paths[:args.max_shapes]
    shape_names = [shape_path.split(os.sep)[-1].split('.')[0] for shape_path in shape_paths]    
    logging.info(str(len(shape_paths)) + ' models to be converted')
    tasks = [(args.shape_dir, args.graph_dir, shape_name) for shape_name in shape_names]
    if args.workers == 1:
        results = [generate_graph(t) for t in tasks]
    else:
        results = Pool(processes=None if args.workers == 0 else args.workers).map(generate_graph, tasks)

    converted = sum(1 for r in results if r == 1)
    skipped = sum(1 for r in results if r == 0)
    failed = sum(1 for r in results if r == -1)
    logging.info(str(converted) + ' models converted')
    logging.info(str(skipped) + ' models skipped (already exist)')
    logging.info(str(failed) + ' models failed')
