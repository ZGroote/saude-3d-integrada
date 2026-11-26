# Referências do Repositório

> Lista restrita às referências efetivamente citadas nos arquivos do repositório (`LICENCAS.md`, `teste-anatomia/LEIAME.md`, `bodyparts3d/RELATORIO.md`, `hra/LICENCA_HRA.md`, `hra/totalseg/LEIAME.md`, `supabase/dados/LEIAME_CID10.md`).

1. **TotalSegmentator** (`teste-anatomia/LEIAME.md`, `LICENCAS.md`):
   Wasserthal J. et al., *"TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT Images"*, Radiology: Artificial Intelligence, 2023. Dataset *"Small subset of TotalSegmentator Dataset"* v2.0.1, University Hospital Basel — <https://zenodo.org/records/10047263> (caso `s1371`).
   Repositório / subtasks (`hra/totalseg/LEIAME.md`): <https://github.com/wasserth/TotalSegmentator#subtasks>.

2. **BodyParts3D** (`LICENCAS.md`, `bodyparts3d/RELATORIO.md`):
   Database Center for Life Science (DBCLS). *BodyParts3D release 4.0* (dados de 2013-06-19; página de licença atualizada em 2025-02-27): <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html>.

3. **Human Reference Atlas (HRA) — United Female** (`LICENCAS.md`, `hra/LICENCA_HRA.md`):
   Browne, Kristen, and Heidi Schlehlein. 2026. *3D Reference Organ Set for Female, v1.10*. <https://doi.org/10.48539/HBM637.DWBM.744> (HuBMAP ID `HBM637.DWBM.744`, biblioteca <https://humanatlas.io/3d-reference-library>).

4. **HuBMAP CCF 3D Reference Object Library** (`hra/LICENCA_HRA.md`):
   Browne, Kristen, Heidi Schlehlein, Bruce W. Herr II, Ellen Quardokus, Andreas Bueckle, and Katy Börner. 2026. *HuBMAP CCF 3D Reference Object Library*. <https://humanatlas.io/3d-reference-library>.

5. **Visible Human Dataset (NLM)** (`hra/LICENCA_HRA.md`, `LICENCAS.md`):
   Spitzer & Whitlock (2002), citado no README do HRA (`hra/LICENCA_HRA.md`). Referência bibliográfica completa **a verificar na fonte original** (não reproduzida aqui para não citar de memória).
   Termos e dados NLM: <https://www.nlm.nih.gov/research/visible/visible_human.html>, <https://www.nlm.nih.gov/research/visible/getting_data.html>, <https://www.nlm.nih.gov/databases/download/terms_and_conditions.html>.

6. **CID-10 (DATASUS / CBCD / OMS)** (`supabase/dados/LEIAME_CID10.md`):
   DATASUS / Centro Brasileiro de Classificação de Doenças (CBCD / FSP-USP) / OMS. *CID-10 Versão 2008* — <http://www2.datasus.gov.br/cid10/V2008/cid10.htm>, tabelas em <http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip>, copyright em <http://www2.datasus.gov.br/cid10/V2008/copyright.htm>.

7. **University of Denver — Visible Human Female STL Models** (`hra/denver/RELATORIO.md`, `hra/denver/bruto/MetaData/README.txt`):
   Andreassen, T. E., Hume, D. R., Hamilton, L. D., Walker, K. E., Higinbotham, S. E., & Shelburne, K. B. 2022. *"Three-dimensional lower extremity musculoskeletal geometry of the Visible Human Female and Male."* *Scientific Data*, DOI <https://doi.org/10.1038/s41597-022-01905-2>. Dataset DOI <https://doi.org/10.56902/COB.vh.2022.1> (<https://digitalcommons.du.edu/visiblehuman/1/>).
   Andreassen, T. E. et al. 2022. *"An Automated Process for 2D and 3D Finite Element Overclosure and Gap Adjustment using Radial Basis Function Networks."* arXiv:2209.06948 (<https://doi.org/10.48550/arXiv.2209.06948>); e *Medical Engineering & Physics*, 2024 (<https://doi.org/10.1016/j.medengphy.2024.104136>).

8. **FIPAT / IFAA — Terminologia Anatomica (TA2)** (`EXP-0013`):
   Federative International Programme for Anatomical Terminology (FIPAT). *Terminologia Anatomica (TA2)*: <https://ta2viewer.openanatomy.org/> e <https://fipat.library.dal.ca/ta2/> (licença `CC BY-ND 4.0` observada via índice de busca web; acesso direto a `fipat.library.dal.ca` não verificado por falha de DNS).

9. **IT'IS Foundation — Virtual Family v2.0 (Ella)** (`EXP-0013`):
   IT'IS Foundation. *Ella V2.0* (<https://itis.swiss/virtual-population/virtual-population/vip2/ella/>, DOI <https://doi.org/10.13099/ViP-Ella-V2.0>), *Terms and Conditions of User License Virtual Family v2.0* (`LicenseAgreementv2-0_2024.pdf`) e `VF2-0_tissue-list.txt`; citação exigida no contrato: Gosselin MC et al., *Physics in Medicine and Biology*, 59(18): 5287-5303, 2014.

9. **HuBMAP HRA Registration SOP & BodyParts3D Reference** (`EXP-0013`):
   HuBMAP HRA SOP *"Managing Human Reference Atlas Registrations"*, DOI <https://doi.org/10.5281/zenodo.11625379>.
   Mitsuhashi, N. et al. 2009. *"BodyParts3D: 3D structure database for anatomical concepts."* *Nucleic Acids Research*, DOI <https://doi.org/10.1093/nar/gkn613>.

10. **Ferramentas abertas de registro, malha, métricas e terminologia** (`EXP-0013`):
    - `probreg` (<https://github.com/neka-nat/probreg>), `pycpd` (<https://github.com/siavashk/pycpd>), `trimesh` (<https://github.com/mikedh/trimesh>), `Open3D` (<https://github.com/isl-org/Open3D>) — MIT License.
    - `ANTs` / `ANTsPy` (<https://github.com/ANTsX/ANTsPy>), `ITKElastix` (<https://github.com/InsightSoftwareConsortium/ITKElastix>), `SimpleITK` (<https://github.com/SimpleITK/SimpleITK>), `surface-distance` (<https://github.com/google-deepmind/surface-distance>), `MONAI` (<https://github.com/Project-MONAI/MONAI>) — Apache-2.0.
    - `3D Slicer` (<https://github.com/Slicer/Slicer/blob/main/License.txt>) — 3D-Slicer-1.0; `PyMeshLab` (<https://github.com/cnr-isti-vclab/PyMeshLab>) — GPLv3.
    - `Wikidata` (<https://www.wikidata.org/wiki/Wikidata:Licensing>), `DeCS/BIREME` (<https://decs.bvsalud.org/>), `SBA` (<https://sbanatomia.org.br/>), `Z-Anatomy` (<https://github.com/Z-Anatomy/Models-of-human-anatomy>), `MedShapeNet` (<https://doi.org/10.5281/zenodo.10623506>), `NIH 3D 3DPX-017237` (<https://3d.nih.gov/entries/3DPX-017237>).
