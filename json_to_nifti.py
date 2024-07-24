import nibabel as nib
import numpy as np
import json
import os
from skimage.draw import polygon

# Function to create a 2D mask from polygon coordinates
def create_mask_from_polygon(coords, shape):
    mask = np.zeros(shape, dtype=np.uint8)
    rr, cc = polygon(np.array(coords)[:, 1], np.array(coords)[:, 0], shape)
    mask[rr, cc] = 1
    return mask

# Main function to convert JSON annotations to a rotated NIfTI
def convert_annotations_to_rotated_nii(json_folder, input_nii_file, output_nii_file_rotated):
    # Load the input NIfTI file to get header and dimensions
    nii_img = nib.load(input_nii_file)
    header = nii_img.header
    affine = nii_img.affine
    scan_data = nii_img.get_fdata()
    
    # Get the dimensions of the scan
    scan_shape = scan_data.shape
    
    # Create an empty 3D volume for the annotations
    annotated_volume_rotated = np.zeros(scan_shape, dtype=np.uint8)
    
    # Get a list of all JSON files in the folder
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    
    # Sort the JSON files to ensure correct order
    json_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    
    # Loop through all JSON files
    for json_filename in json_files:
        with open(os.path.join(json_folder, json_filename), 'r') as f:
            data = json.load(f)
        
        # Extract slice number from filename
        slice_num = int(json_filename.split('_')[-1].split('.')[0])
        
        for obj in data['objects']:
            segmentation = obj['segmentation']
            mask = create_mask_from_polygon(segmentation, (scan_shape[0], scan_shape[1]))
            
            # Rotate the mask 90 degrees clockwise
            rotated_mask = np.rot90(mask, k=-1)
            
            # Update the 3D volume with the rotated mask
            annotated_volume_rotated[:, :, slice_num] = np.maximum(annotated_volume_rotated[:, :, slice_num], rotated_mask)
    
    # Save the annotated volume as a new NIfTI file
    annotated_nii_rotated = nib.Nifti1Image(annotated_volume_rotated, affine, header)
    nib.save(annotated_nii_rotated, output_nii_file_rotated)

'''
# Example usage
json_folder = 'ori_flair_jpg'
input_nii_file = 'ori_flair.nii.gz'
output_nii_file_rotated = 'segmentation_rotated.nii.gz'

convert_annotations_to_rotated_nii(json_folder, input_nii_file, output_nii_file_rotated)

'''