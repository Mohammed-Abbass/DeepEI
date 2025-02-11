# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 14:25:33 2019

@author: hcji
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.sparse import load_npz, csr_matrix
from libmetgem import msp
from tqdm import tqdm
from rdkit import Chem
from DeepEI.utils import get_cdk_fingerprints, get_fp_score
from DeepEI.predict import predict_fingerprint


with open('DeepEI/data/split.json', 'r') as js:
    split = json.load(js)
keep = np.array(split['keep'])

nist_smiles = np.array(json.load(open('DeepEI/data/all_smiles.json')))[keep]
nist_masses = np.load('DeepEI/data/molwt.npy')[keep]
nist_fingerprint = load_npz('DeepEI/data/fingerprints.npz').todense()[keep,:]

neims_msbk_smiles = np.array(json.load(open('DeepEI/data/neims_msbk_smiles.json')))
neims_msbk_masses = np.load('DeepEI/data/neims_msbk_masses.npy')
neims_msbk_cdkfps = load_npz('DeepEI/data/neims_msbk_cdkfps.npz').todense()

msbk_smiles = np.array(json.load(open('DeepEI/data/msbk_smiles.json')))
msbk_masses = np.load('DeepEI/data/msbk_masses.npy')
msbk_spec = load_npz('DeepEI/data/msbk_spec.npz').todense()

mlp = pd.read_csv('Fingerprint/results/mlp_result.txt', sep='\t', header=None)
mlp.columns = ['id', 'accuracy', 'precision', 'recall', 'f1']
fpkeep = mlp['id'][np.where(mlp['f1'] > 0.5)[0]]
pred_fps = predict_fingerprint(msbk_spec, fpkeep) 

db_smiles = np.array(list(neims_msbk_smiles) + list(nist_smiles))
db_masses = np.append(neims_msbk_masses, nist_masses)
db_fingerprints = np.append(neims_msbk_cdkfps, nist_fingerprint, axis=0)[:, fpkeep]
'''
nist_onbit = np.squeeze(np.asarray(np.sum(nist_fingerprint[:, fpkeep], axis=1)))
msbk_onbit = np.squeeze(np.asarray(np.sum(neims_msbk_cdkfps[:, fpkeep], axis=1)))
plt.figure(figsize=(8, 6))
plt.violinplot( [nist_onbit, msbk_onbit] , showmeans=False, showmedians=True)
plt.xticks([1, 2], ['NIST', 'MassBank'])
plt.ylabel('Number of On-bit Fingerprints')
'''
if __name__ == '__main__':
    
    output = pd.DataFrame(columns=['smiles', 'mass', 'fp_score', 'rank', 'candidates', 'inNIST'])
    for i, smi in enumerate(tqdm(msbk_smiles)):
        mass = msbk_masses[i]
        pred_fp = pred_fps[i]
        incl = smi in nist_smiles
        
        candidate = np.where(np.abs(db_masses - mass) < 5)[0] # candidates  
        cand_smi = db_smiles[candidate]
        try:
            wh_true = np.where(cand_smi == smi)[0][0]
        except:
            continue

        scores = get_fp_score(pred_fp, db_fingerprints[candidate, :]) # scores of all candidtates
        true_score = scores[wh_true]
        rank = len(np.where(scores > true_score)[0]) + 1
        
        output.loc[len(output)] = [smi, mass, true_score, rank, len(candidate), incl]
        output.to_csv('Discussion/results/DeepEI_massbank_B.csv')
        