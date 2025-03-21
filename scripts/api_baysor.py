import sopa
from spatialdata import read_zarr
import os
import sys
import toml
from os.path import join

confidence = float(sys.argv[2])
base_segmentation = sys.argv[1]
sample = sys.argv[3]

def main(base_segmentation, confidence, sample):
    """Run segmentation."""
    path = f"/dss/dssfs03/pn52re/pn52re-dss-0001/cellseg-benchmark/samples/{sample}/results"
    sdata = read_zarr(join(path, join(base_segmentation, "sdata.zarr")))
    
    sopa.make_transcript_patches(sdata, patch_width=1000, patch_overlap=20, prior_shapes_key="cellpose_boundaries")
    
    sopa.settings.parallelization_backend = "dask"
    sopa.settings.dask_client_kwargs["n_workers"] = int(os.getenv('SLURM_JOB_NUM_NODES', 1)) * int(os.getenv('SLURM_NTASKS_PER_NODE', 1))
    
    path_toml = "/dss/dssfs03/pn52re/pn52re-dss-0001/cellseg-benchmark/misc/baysor_2D_config.toml"
    with open(path_toml, 'r') as f:
        config = toml.load(f)
    config["segmentation"]["prior_segmentation_confidence"] = confidence
    sopa.segmentation.baysor(sdata, config=config, delete_cache=True)
    
    sopa.aggregate(sdata, gene_column="gene", average_intensities=True, min_transcripts=10)
    sopa.io.explorer.write(join(path, join(f"Baysor_2D_{base_segmentation}_{confidence}", "sdata.explorer")), sdata, gene_column="gene", ram_threshold_gb=4, pixel_size=0.108)
    
    del sdata[list(sdata.images.keys())[0]], sdata[list(sdata.points.keys())[0]]
    sdata.write(join(path, join(f"Baysor_2D_{base_segmentation}_{confidence}", "sdata.zarr"))

if __name__ == "__main__":
    main(base_segmentation, confidence, sample)
