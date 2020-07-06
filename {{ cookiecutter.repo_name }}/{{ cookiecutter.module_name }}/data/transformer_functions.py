import pathlib

from sklearn.model_selection import train_test_split

from . import Dataset

__all__ = [
    'sklearn_train_test_split',
    'sklearn_transform',
]


def sklearn_train_test_split(ds_dict, **split_opts):
    """Transformer Function: performs a train/test split.

    for each `dset` in ds_dict, this transformer creates two new
    datasets: {dset.name}_test and {dset.name}_train

    Parameters
    ----------
    ds_dict:
        input datasets
    **split_opts:
        Remaining options will be passed to `train_test_split`

    """
    new_ds = {}
    for ds_name, dset in ds_dict.items():

        for kind in ['train', 'test']:
            dset_name = f"{dset_name}_{kind}"
            dset_meta = {**dset.metadata, 'split':kind, 'split_opts':split_opts}
            new_ds[dset_name] = Dataset(dataset_name=dset_name, metadata=dset_meta)
        X_train, X_test, y_train, y_test = train_test_split(dset.data, dset.target, **split_opts)

        new_ds[f'{dset_name}_train'].data = X_train
        new_ds[f'{dset_name}_train'].target = y_train
        new_ds[f'{dset_name}_test'].data = X_test
        new_ds[f'{dset_name}_test'].target = y_test
    return new_ds

def sklearn_transform(ds_dict, transformer_name, transformer_opts=None, subselect_column=None, **opts):
    """
    Wrapper for any 1:1 (data in to data out) sklearn style transformer. Will run the .fit_transform
    method of the transformer on dset.data. If subselect_column is not None, it will treat the data
    like a dataframe and will subselect dset.data[subselect_column] to run the transformer on.

    Parameters
    ----------
    ds_dictet:
        Datasets upon which to apply transforms
    transformer_name: string
        sklearn style transformer with a .fit_transform method avaible via sklearn_transformers.
    transformer_opts: dict
        options to pass on to the transformer
    subselect_column: string
        column name for dset.data to run the transformer on
    return_whole: boolean
        return the whole dataframe with a new column named "transformed"
    **opts:
        options to pass on to the fit_transform method

    Returns
    -------
    Datasets whose data are the result of the transformer.fit_transform
    """
    new_dsdict = {}
    for ds_name, dset in ds_dict.items():
        if transformer_name in sklearn_transformers():
            transformer = sklearn_transformers(keys_only=False).get(transformer_name)(**transformer_opts)
        else:
            raise ValueError(f"Invalid transformer name: {transformer_name}. See sklearn_transformers for available names.")
        if subselect_column:
            new_data = transformer.fit_transform(dset.data[subselect_column], **opts)
        else:
            new_data = transformer.fit_transform(dset.data, **opts)

        new_dsname = f"{dset.name}_{transformer.__class__.__name__}"
        new_dsdict[new_dsname] = Dataset(dataset_name=new_dsname, metadata=dset.metadata, data=new_data)
    return new_dsdict
