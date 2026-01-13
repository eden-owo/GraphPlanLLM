"""
Demo script showing how to use ImageProcessor with custom uploaded images.

Usage:
    python demo_image_upload.py path/to/your/image.png
"""

import sys
import matplotlib.pyplot as plt
from image_processor import ImageProcessor
from app import App
from g2p.plot import plot_fp

# Configuration paths
MODEL_PATH = '../Interface/model/model.pth'
DEVICE = 'cuda'
TRAIN_PATH = '../Interface/static/Data/data_train_converted.pkl'
TF_PATH = '../Interface/retrieval/tf_train.npy'
CENTROID_PATH = '../Interface/retrieval/centroids_train.npy'
CLUSTER_PATH = '../Interface/retrieval/clusters_train.npy'

def main(image_path):
    """Process custom image and generate floor plan."""
    
    print("=" * 60)
    print("Graph2Plan - Custom Image Upload Demo")
    print("=" * 60)
    
    # Initialize
    print("\n[1/6] Initializing...")
    app = App(MODEL_PATH, DEVICE, TRAIN_PATH, TF_PATH, CENTROID_PATH, CLUSTER_PATH)
    processor = ImageProcessor()
    print("✓ Complete")
    
    # Process image
    print(f"\n[2/6] Processing image: {image_path}")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    data_boundary = processor.process_image(image_bytes)
    print(f"✓ Extracted {len(data_boundary.boundary)} boundary points")
    
    # Retrieve
    print("\n[3/6] Retrieving similar floor plans...")
    data_graph = app.retrieve(data_boundary, k=10)[0]
    print("✓ Retrieved")
    
    # Generate
    print("\n[4/6] Generating floor plan...")
    data = app.transfer(data_boundary, data_graph)
    data = app.forward(data, network_data=False)
    data = app.align(data)
    data = app.decorate(data)
    print(f"✓ Generated ({len(data.rType)} rooms)")
    
    # Visualize
    print("\n[5/6] Visualizing...")
    ax = plot_fp(data.boundary, data.newBox[data.order], 
                 data.rType[data.order], data.doors, data.windows)
    
    output_path = 'demo_result.png'
    plt.gcf().canvas.print_figure(output_path)
    print(f"✓ Saved to {output_path}")
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python demo_image_upload.py <image_path>")
        sys.exit(1)
    
    main(sys.argv[1])
