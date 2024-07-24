import os
import nibabel as nib
import numpy as np
from PIL import Image

def nifti_to_jpg(input_file, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Load the NIfTI file
    nifti_img = nib.load(input_file)
    nifti_data = nifti_img.get_fdata()

    # Get the shape of the data
    shape = nifti_data.shape
    print(f"NIfTI data shape: {shape}")

    # Determine which dimension to iterate over
    if len(shape) == 4:
        slice_dim = 3  # For 4D data, assume time is the 4th dimension
    elif len(shape) == 3:
        slice_dim = 2  # For 3D data, use the 3rd dimension
    else:
        raise ValueError("Unexpected number of dimensions in NIfTI data")

    # Process each slice
    for i in range(shape[slice_dim]):
        # Extract the slice
        if len(shape) == 4:
            slice_data = nifti_data[:, :, :, i]
        else:
            slice_data = nifti_data[:, :, i]

        # Normalize the data to 0-255 range
        slice_data = ((slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255).astype(np.uint8)

        # Ensure the slice is 2D
        if len(slice_data.shape) > 2:
            slice_data = np.mean(slice_data, axis=2)  # Convert to grayscale if it's RGB

        # Convert to 3 channels
        slice_data = np.stack((slice_data,) * 3, axis=-1)
	
	# Rotate the image by 90 degrees anti-clockwise
        slice_data = np.rot90(slice_data)
        
        # Create a PIL Image
        img = Image.fromarray(slice_data)

        # Save as JPG
        output_file = os.path.join(output_folder, f'slice_{i:03d}.jpg')
        img.save(output_file, 'JPEG', quality=95)

    print(f"Conversion complete. JPG files saved in {output_folder}")

'''
# Example usage
input_file = 'ori_flair.nii.gz'
output_folder = 'ori_flair_jpg'

nifti_to_jpg(input_file, output_folder)
'''