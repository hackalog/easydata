import os
import pathlib

# Get the project directory as the parent of this module location
src_module_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
project_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent

data_path = project_dir / 'data'

raw_data_path = data_path / 'raw'
interim_data_path = data_path / 'interim'
processed_data_path = data_path / 'processed'

model_path = project_dir / 'models'
trained_model_path = model_path / 'trained'
model_output_path = model_path / 'output'

analysis_path = project_dir / 'reports'
summary_path = analysis_path / 'summary'
tables_path = analysis_path / 'tables'
figures_path = analysis_path / 'figures'

reports_path = project_dir / 'reports'
