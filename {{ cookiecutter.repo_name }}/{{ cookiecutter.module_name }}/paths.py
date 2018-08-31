import os
import pathlib

# Get the project directory as the parent of this module location
project_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent
                          
data_path = project_dir / 'data'

raw_data_path = data_path / 'raw'
interim_data_path = data_path / 'interim'
processed_data_path = data_path / 'processed'

model_path = project_dir / 'models'

trained_model_path = model_path / 'trained'
model_output_path = model_path / 'predictions'
analysis_path = model_path / 'analysis'
