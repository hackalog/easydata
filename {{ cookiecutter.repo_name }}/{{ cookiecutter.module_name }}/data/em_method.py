import numpy as np
import scipy.sparse
import numba

@numba.njit(
    locals={
        "all_data": numba.types.float64[::1],
        "data": numba.types.float64[::1],
        "ind": numba.types.int32[::1],
        "p": numba.types.float64[::1],
        "bg": numba.types.float64[::1],
        "word_posterior": numba.types.float64[::1],
        "s": numba.types.float64,
        "new_s": numba.types.float64,
        "new_p_sum": numba.types.float64,
        "new_p_cnt": numba.types.float64[::1],
        "pfull": numba.types.float64[::1],
        "dparam": numba.types.float64,
        "dparam_vec": numba.types.float64[::1],
        "pfull_new": numba.types.float64[::1],
    }
)

def numba_em_sparse(all_data, all_indices, all_indptr, bg_full, precision=1e-4, low_thresh=1e-5, prior_noise=1.0):
    """
    The numba version of em_sparse. 
    
    For each row R of the matrix mat, find a float, s, and vector M, such that R ~ sM + (1-s)BG where BG is the L1
    normalization of the column sums of mat.

    Here all_data, all_indices, all_indptr are data that represent a scipy sparse matrix mat.

    Parameters
    ----------
    all_data: mat.data
    all_indices: mat.indices
    all_indptr: mat.indptr
    bg_full: 
        column weights of mat
    precision: float Default 1e-4
        The accuracy for computing s
    low_thresh: float Default 1e-4
        Replace entries below low_thresh with 0's
    prior_noise: float Default 1.0
        Sets the Beta prior on s to be Beta(1, prior_noise)

    Returns
    -------
    (M, s)
    The matrix with rows M, and an array s.
    """
    assert len(all_data) > 0

    # Set up
    new_data = np.zeros(all_data.shape[0])
    s_array = np.zeros(len(all_indptr)-1)

    prior = np.array([1.0, prior_noise])
    mp = 1.0 + 1.0 * np.sum(prior)

    for i in range(len(all_indptr)-1):
        ind = all_indices[all_indptr[i] : all_indptr[i+1]]
        data = all_data[all_indptr[i] : all_indptr[i+1]]

        assert(np.max(data) > 0.0)
        assert(np.min(data) >= 0.0)

        bg = bg_full[ind]
        bg /= np.sum(bg)

        # initial guess
        s = 0.5
        p = s*data + (1 -s)*bg

        pfull = p*s + (1-s)*bg
        dparam = precision + 1.0
        dparam_vec = pfull

        # Run EM
        while dparam > precision and s > precision and s < (1.0 - precision):
            word_posterior = (p * s) / (p * s + bg * (1-s))
            new_p_cnt = word_posterior * data
            new_p_sum = np.sum(new_p_cnt)
            new_p = new_p_cnt / new_p_sum
            new_s = (new_p_sum + prior[0]) / mp

            pfull_new = new_p * new_s + bg * (1 - new_s)

            dparam_vec = np.abs(pfull_new - pfull)
            dparam_vec /= pfull
            dparam = np.sum(dparam_vec)
            pfull = pfull_new

            # zero out small values
            while np.sum((new_p < low_thresh) & (new_p != 0.0)) > 0:
                new_p[new_p < low_thresh] = 0.0
                new_p /= np.sum(new_p)

            p = new_p
            s = new_s

        new_data[all_indptr[i]: all_indptr[i+1]] = p
        s_array[i] = s

    return new_data, s_array





def em_sparse(mat, precision=1e-4, low_thresh=1e-5, prior_noise=1.0):
    """
    For each row R of the matrix mat, find s and  M, such that R ~ sM + (1-s)BG where BG is the L1
    normalization of the column sums of mat. 

    Parameters
    ----------
    mat: scipy sparse matrix
    precision: float Default 1e-4
        The accuracy for computing s
    low_thresh: float Default 1e-5
        Replace entries below low_thresh with 0's
    prior_noise: float Default 1.0
        Sets the Beta prior on s to be Beta(1, prior_noise)

    Returns
    -------
    (M, s)
    The matrix with rows M, and an array s.
    """
    new_mat = mat.copy().tocsr().astype(np.float64)
    col_sum = np.array(mat.sum(axis=0))[0]
    col_weights = (col_sum.astype(np.float64)) / np.sum(col_sum)
    numba_data, s_array = numba_em_sparse(new_mat.data,
                                        new_mat.indices,
                                        new_mat.indptr,
                                        col_weights,
                                        precision=precision,
                                        low_thresh=low_thresh,
                                        prior_noise=prior_noise)
    new_mat.data = numba_data
    new_mat.eliminate_zeros()
    return new_mat, s_array
