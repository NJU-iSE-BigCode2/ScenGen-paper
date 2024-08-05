from os.path import join as p_join
import time
from typing import Dict, Any

import testbot.uied.detect_compo.lib_ip.ip_preprocessing as pre
import testbot.uied.detect_compo.lib_ip.ip_draw as draw
import testbot.uied.detect_compo.lib_ip.ip_detection as det
import testbot.uied.detect_compo.lib_ip.file_utils as file
import testbot.uied.detect_compo.lib_ip.Component as Compo
from testbot.uied.CONFIG_UIED import Config

C = Config()


def nesting_inspection(org, grey, compos, ffl_block):
    """
    Inspect all big compos through block division by flood-fill
    :param ffl_block: gradient threshold for flood-fill
    :return: nesting compos
    """
    nesting_compos = []
    for i, compo in enumerate(compos):
        if compo.height > 50:
            replace = False
            clip_grey = compo.compo_clipping(grey)
            n_compos = det.nested_components_detection(clip_grey, org, grad_thresh=ffl_block, show=False)
            Compo.cvt_compos_relative_pos(n_compos, compo.bbox.col_min, compo.bbox.row_min)

            for n_compo in n_compos:
                if n_compo.redundant:
                    compos[i] = n_compo
                    replace = True
                    break
            if not replace:
                nesting_compos += n_compos
    return nesting_compos


def compo_detection(
        img_path: str,
        output_root: str,
        uied_params: Dict[str, Any],
        resize_by_height: int = 800,
        wait_key: int = 0,
        show: bool = False,
):

    start = time.perf_counter()
    name = img_path.split("/")[-1][:-4] if "/" in img_path else img_path.split("\\")[-1][:-4]
    ip_root = file.build_directory(p_join(output_root, "ip"))

    # *** Step 1 *** pre-processing: read img -> get binary map
    org, grey = pre.read_img(
        path=img_path,
        resize_height=resize_by_height,
        kernel_size=None,  # for medianBlur
    )
    binary = pre.binarization(
        org=org, grad_min=int(uied_params["min-grad"])
    )

    # *** Step 2 *** element detection
    det.rm_line(binary=binary, show=show, wait_key=wait_key)
    ui_compos = det.component_detection(
        binary=binary, min_obj_area=int(uied_params["min-ele-area"]),
    )

    # *** Step 3 *** results refinement
    ui_compos = det.compo_filter(
        compos=ui_compos, min_area=int(uied_params["min-ele-area"]), img_shape=binary.shape
    )
    ui_compos = det.merge_intersected_compos(compos=ui_compos)
    det.compo_block_recognition(binary=binary, compos=ui_compos)
    if uied_params["merge-contained-ele"]:
        ui_compos = det.rm_contained_compos_not_in_block(compos=ui_compos)
    Compo.compos_update(compos=ui_compos, org_shape=org.shape)
    Compo.compos_containment(compos=ui_compos)

    # *** Step 4 ** nesting inspection: check if big compos have nesting element
    ui_compos += nesting_inspection(
        org=org, grey=grey, compos=ui_compos, ffl_block=uied_params["ffl-block"]
    )
    Compo.compos_update(compos=ui_compos, org_shape=org.shape)
    draw.draw_bounding_box(
        org=org, components=ui_compos, show=show, name="merged compo",
        write_path=p_join(ip_root, name + ".jpg"), wait_key=wait_key
    )

    # *** Step 5 *** save detection result
    Compo.compos_update(compos=ui_compos, org_shape=org.shape)
    file.save_corners_json(file_path=p_join(ip_root, name + ".json"), compos=ui_compos)
    # print("[Compo Detection Completed in %.3f s] Input: %s Output: %s" % (time.perf_counter() - start, img_path, p_join(ip_root, name + ".json")))
