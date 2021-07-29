import configparser
from math import pi
import pandas as pd


class ConcentrationInflow:
    def __init__(self, file):
        csv_file = pd.read_csv(file, sep=';')
        self.cin_nh4 = csv_file['nh4'].tolist()
        self.cin_no3 = csv_file['no3'].tolist()
        self.cin_o2 = csv_file['o2'].tolist()
        self.cin_doc = csv_file['doc'].tolist()


class GeneralParameters:
    def __init__(self, setup_file):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Ew = float(setup['GENERAL']['Ew'])
        self.Kc = float(setup['GENERAL']['Kc'])  # verificar esse valor antes de rodar
        self.Df = float(setup['GENERAL']['Df'])
        self.Dw = float(setup['GENERAL']['Dw'])
        self.Dt = float(setup['GENERAL']['Dt'])
        self.Dg = float(setup['GENERAL']['Dg'])
        self.L = float(setup['GENERAL']['L'])
        self.nf = float(setup['GENERAL']['nf'])
        self.nw = float(setup['GENERAL']['nw'])
        self.nt = float(setup['GENERAL']['nt'])
        self.ng = float(setup['GENERAL']['ng'])
        self.nn = float(setup['GENERAL']['nn'])
        self.rwv = float(setup['GENERAL']['rwv'])
        self.dt = float(setup['TIMESTEP']['dt'])
        self.n = int(setup['MODEL']['n'])
        self.dz = self.L / self.n
        self.d50 = float(setup['MODEL']['d50'])
        self.k_nit = float(setup['NITRIFICATION']['k_nit'])
        self.k_denit = float(setup['DENITRIFICATION']['k_denit'])


class PondingZone:
    def __init__(self, setup_file):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Ab = float(setup['PONDING_ZONE']['Ap'])
        self.Hover = float(setup['PONDING_ZONE']['Hover'])
        self.Kweir = float(setup['PONDING_ZONE']['Kweir'])
        self.wWeir = float(setup['PONDING_ZONE']['wWeir'])
        self.expWeir = float(setup['PONDING_ZONE']['expWeir'])
        self.Cs = float(setup['PONDING_ZONE']['Cs'])
        self.Pp = float(setup['PONDING_ZONE']['Pp'])
        self.flagp = float(setup['PONDING_ZONE']['flagp'])
        self.k_denit_pz = float(setup['DENITRIFICATION']['k_denit_pz'])


class UnsaturatedZone:
    def __init__(self, setup_file, L, hpipe, dz):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.A = float(setup['UNSATURATED_ZONE']['A'])
        self.husz_ini = float(setup['UNSATURATED_ZONE']['husz'])
        self.nusz_ini = float(setup['UNSATURATED_ZONE']['nusz'])
        self.Ks = float(setup['UNSATURATED_ZONE']['Ks'])
        self.sh = float(setup['UNSATURATED_ZONE']['sh'])
        self.sw = float(setup['UNSATURATED_ZONE']['sw'])
        self.sfc = float(setup['UNSATURATED_ZONE']['sfc'])
        self.ss = float(setup['UNSATURATED_ZONE']['ss'])
        self.gama = float(setup['UNSATURATED_ZONE']['gama'])
        self.Kf = float(setup['UNSATURATED_ZONE']['Kf'])
        self.m_usz = round((L - hpipe) / dz)

    def f_alfa_beta(self, layer):
        alfa = (self.m_usz - 1 - layer) / (self.m_usz - 1)
        beta = layer / (self.m_usz - 1)
        return alfa, beta

    def f_unit_flux(self, alfa, beta, I1, Qet_1, I2, Qhc, Qorif, Qinf_sz, teta_sm_i, hpipe, Ab):
        if hpipe > 0:
            unit_flux = (alfa * (I1 - Qet_1) + beta * (I2 - Qhc)) / (Ab * teta_sm_i)
        else:
            unit_flux = (alfa * (I1 - Qet_1) + beta * (Qorif + Qinf_sz - Qhc)) / (Ab * teta_sm_i)
        return unit_flux

    def f_peclet(self, unit_flux, D, dz):
        if D > 0:
            peclet = unit_flux * dz / D
        else:
            peclet = 100
        return peclet


class SaturatedZone:
    def __init__(self, setup_file, n, m_usz):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Psz = float(setup['SATURATED_ZONE']['Psz'])
        self.hpipe = float(setup['SATURATED_ZONE']['hpipe'])
        self.flagsz = float(setup['SATURATED_ZONE']['flagsz'])
        self.dpipe = float(setup['SATURATED_ZONE']['dpipe'])
        self.Cd = float(setup['SATURATED_ZONE']['Cd'])
        self.Apipe = pi * (self.dpipe / (1000 * 2)) ** 2
        self.m_sz = n - m_usz

    def f_alfa_beta(self, layer):
        alfa = (self.m_sz - 1 - layer) / (self.m_sz - 1)
        beta = layer / (self.m_sz - 1)
        return alfa, beta

    def f_unit_flux(self, alfa, beta, I2, Qhc, Qet_2, Qorif, Qinf_sz, teta_b_i, Ab):
        unit_flux = (alfa * (I2 - Qhc - Qet_2) + beta * (Qorif + Qinf_sz)) / (Ab * teta_b_i)
        return unit_flux

    def f_peclet(self, unit_flux, D, dz):
        if D > 0:
            peclet = unit_flux * dz / D
        else:
            peclet = 100
        return peclet




class Calibration:
    def __init__(self, setup_file):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Kc_min = float(setup['FLOW_CALIBRATION']['Kc_min'])
        self.Kc_max = float(setup['FLOW_CALIBRATION']['Kc_max'])
        self.Ks_min = float(setup['FLOW_CALIBRATION']['Ks_min'])
        self.Ks_max = float(setup['FLOW_CALIBRATION']['Ks_max'])
        self.sh_min = float(setup['FLOW_CALIBRATION']['sh_min'])
        self.sh_max = float(setup['FLOW_CALIBRATION']['sh_max'])
        self.sw_min = float(setup['FLOW_CALIBRATION']['sw_min'])
        self.sw_max = float(setup['FLOW_CALIBRATION']['sw_max'])
        self.sfc_min = float(setup['FLOW_CALIBRATION']['sfc_min'])
        self.sfc_max = float(setup['FLOW_CALIBRATION']['sfc_max'])
        self.ss_min = float(setup['FLOW_CALIBRATION']['ss_min'])
        self.ss_max = float(setup['FLOW_CALIBRATION']['ss_max'])
        self.Kf_min = float(setup['FLOW_CALIBRATION']['Kf_min'])
        self.Kf_max = float(setup['FLOW_CALIBRATION']['Kf_max'])
        self.Cd_min = float(setup['FLOW_CALIBRATION']['Cd_min'])
        self.Cd_max = float(setup['FLOW_CALIBRATION']['Cd_max'])
        self.pop_init = int(setup['FLOW_CALIBRATION']['pop'])
        self.gen_init = int(setup['FLOW_CALIBRATION']['gen'])
        self.obs_file = setup['FLOW_CALIBRATION']['obs_file']
        self.lamta_min = float(setup['QUALITY_CALIBRATION']['lamta_min'])
        self.lamta_max = float(setup['QUALITY_CALIBRATION']['lamta_max'])
        self.kads_nh4_min = float(setup['QUALITY_CALIBRATION']['kads_nh4_min'])
        self.kads_nh4_max = float(setup['QUALITY_CALIBRATION']['kads_nh4_max'])
        self.kdes_nh4_min = float(setup['QUALITY_CALIBRATION']['kdes_nh4_min'])
        self.kdes_nh4_max = float(setup['QUALITY_CALIBRATION']['kdes_nh4_max'])
        self.kads2_nh4_min = float(setup['QUALITY_CALIBRATION']['kads2_nh4_min'])
        self.kads2_nh4_max = float(setup['QUALITY_CALIBRATION']['kads2_nh4_max'])
        self.kdes2_nh4_min = float(setup['QUALITY_CALIBRATION']['kdes2_nh4_min'])
        self.kdes2_nh4_max = float(setup['QUALITY_CALIBRATION']['kdes2_nh4_max'])
        self.k_nit_min = float(setup['QUALITY_CALIBRATION']['k_nit_min'])
        self.k_nit_max = float(setup['QUALITY_CALIBRATION']['k_nit_max'])
        self.k_denit_min = float(setup['QUALITY_CALIBRATION']['k_denit_min'])
        self.k_denit_max = float(setup['QUALITY_CALIBRATION']['k_denit_max'])
        self.D_nh4_min = float(setup['QUALITY_CALIBRATION']['D_nh4_min'])
        self.D_nh4_max = float(setup['QUALITY_CALIBRATION']['D_nh4_max'])
        self.D_no3_min = float(setup['QUALITY_CALIBRATION']['D_no3_min'])
        self.D_no3_max = float(setup['QUALITY_CALIBRATION']['D_no3_max'])
        self.pop_init = int(setup['QUALITY_CALIBRATION']['pop'])
        self.gen_init = int(setup['QUALITY_CALIBRATION']['gen'])
        self.obs_file_nh4 = setup['QUALITY_CALIBRATION']['obs_file_nh4']
        self.obs_file_no3 = setup['QUALITY_CALIBRATION']['obs_file_no3']
        self.show_summary = bool(setup['QUALITY_CALIBRATION']['show_summary'])


class SoilPlant:
    def __init__(self, setup_file, nusz_ini):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.ro_pd = float(setup['SOIL_PLANT']['ro'])
        self.f = float(setup['SOIL_PLANT']['f'])
        self.lamda = float(setup['SOIL_PLANT']['lamda'])
        self.lamta = float(setup['SOIL_PLANT']['lamta'])
        self.root_fraction = float(setup['SOIL_PLANT']['root_fraction'])
        self.c_o2_root = float(setup['SOIL_PLANT']['c_o2_root'])
        self.ro = (1 - nusz_ini) * self.ro_pd


class Nutrient:
    def __init__(self, m_usz, m_sz):
        """
        :param p: parameter object instantiated by the Parameter class .
        """
        self.cp_a = 0
        self.cs_usz_a = 0
        self.cs_sz_a = 0
        self.cp = []
        self.c0_usz = [0] * m_usz
        self.c0_sz = [0] * m_sz
        self.cs0_usz = [self.cs_usz_a] * m_usz
        self.cs0_sz = [self.cs_sz_a] * m_sz
        self.c_usz = [self.c0_usz]
        self.cs_usz = [self.c0_usz]
        self.c_sz = [self.c0_sz]
        self.cs_sz = [self.c0_sz]
        self.Rx_usz = [self.c0_usz]
        self.Rx_sz = [self.c0_sz]
        self.Mstor_ast_list = []  # O passo corretivo é feito com a massa, M indica a massa que vai ser usada no passo corretivo. Ast é asterisco.
        self.Msoil_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.MRx_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Min_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Mover_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Mpipe_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Minfsz_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Met_acum = []  # massa em cada zona para poder calcular no balanço de massa
        self.Mpz_list = []  # massa em cada zona para poder calcular no balanço de massa
        self.Mstor_mb_list = []  # mb mass balance


class Ammonia(Nutrient):
    def __init__(self, m_usz, m_sz, setup_file):
        super(Ammonia, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D_nh4 = float(setup['NH4']['D_nh4'])
        self.kads_nh4 = float(setup['NH4']['kads_nh4'])
        self.kdes_nh4 = float(setup['NH4']['kdes_nh4'])
        self.kads2_nh4 = float(setup['NH4']['kads2_nh4'])
        self.kdes2_nh4 = float(setup['NH4']['kdes2_nh4'])
        self.k_nh4_mb = float(setup['NH4']['k_nh4_mb'])
        self.Fm_nh4 = float(setup['NH4']['Fm_nh4'])
        self.Km_nh4 = float(setup['NH4']['Km_nh4'])


class Nitrate(Nutrient):
    def __init__(self, m_usz, m_sz, setup_file):
        super(Nitrate, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D_no3 = float(setup['NO3']['D_no3'])
        self.Fm_no3 = float(setup['NO3']['Fm_no3'])
        self.Km_no3 = float(setup['NO3']['Km_no3'])


class Oxygen(Nutrient):
    def __init__(self, m_usz, m_sz, setup_file):
        super(Oxygen, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D_o2 = float(setup['O2']['D_o2'])
        self.K_o2 = float(setup['O2']['k_inib_o2'])  # perguntar pq K no lugar de k_inib_02
        self.k_o2 = float(setup['O2']['k_o2'])


class DissolvedOrganicCarbon(Nutrient):
    def __init__(self, m_usz, m_sz, setup_file):
        super(DissolvedOrganicCarbon, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D_doc = float(setup['DOC']['D_doc'])
        self.fb_doc = float(setup['DOC']['fb_doc'])
        self.bDOCd = float(setup['DOC']['bDOCd'])
        self.KbDOC = float(setup['DOC']['KbDOC'])
        self.k_doc = float(setup['DOC']['k_doc'])
        self.kads_doc = float(setup['DOC']['kads_doc'])
        self.kdes_doc = float(setup['DOC']['kdes_doc'])
        self.kads2_doc = float(setup['DOC']['kads2_doc'])
        self.kdes2_doc = float(setup['DOC']['kdes2_doc'])
        self.k_doc_mb = float(setup['DOC']['k_doc_mb'])

