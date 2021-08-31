import configparser
from math import pi
import pandas as pd


class WaterFlowResults:
    def __init__(self, tQrain, tQin, tEmax):
        self.indice = list(range(0, len(tQrain)))
        self.tt = []
        self.tQover = []
        self.tQpf = []
        self.tQinfp = []
        self.tQfs = []
        self.tQhc = []
        self.tQet = []
        self.tQinfsz = []
        self.tQpipe = []
        self.tQet1 = []
        self.tQet2 = []
        self.thp = []
        self.ts = []
        self.thusz = []
        self.thsz = []
        self.thszEST = []
        self.tnsz = []
        self.tnusz = []
        self.thpEND = []
        self.tteta_usz = []
        self.tteta_sz = []
        self.tQin = tQin
        self.tQrain = tQrain
        self.tEmax = tEmax
        self.indice = list(range(0, len(self.tQrain)))

    def water_balance(self, dt):
        Qin_total = self.tQin.sum()
        Qover_total = pd.array(self.tQover).sum()
        Qpipe_total = pd.array(self.tQpipe).sum()
        Qpeak_over = pd.array(self.tQover).max()
        Qpf_total = pd.array(self.tQpf).sum()
        Qfs_total = pd.array(self.tQfs).sum()

        Vtotal_in = Qin_total * dt
        Vtotal_over = Qover_total * dt
        Vtotal_pipe = Qpipe_total * dt
        Vtotal_pf = Qpf_total * dt
        Vtotal_fs = Qfs_total * dt

        Smax = pd.array(self.ts).max()
        hmax = pd.array(self.thp).max()

        print('Vtotal_in :', Vtotal_in)  # m3
        print('Vtotal_over :', Vtotal_over)  # m3
        print('Vtotal_pipe (m3):', Vtotal_pipe)  # m3
        print('Vtotal_pf :', Vtotal_pf)  # m3
        print('Vtotal_fs :', Vtotal_fs)  # m3
        print('Qpeak_over :', Qpeak_over * 1000)  # L/s
        print('Smax :', Smax)  # m3
        print('hmax :', hmax)  # m


class GeneralParameters:
    def __init__(self, setup_file, input_file):
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
        self.hpipe = float(setup['SATURATED_ZONE']['hpipe'])
        self.dpipe = float(setup['SATURATED_ZONE']['dpipe'])
        self.Cd = float(setup['SATURATED_ZONE']['Cd'])
        self.Apipe = pi * (self.dpipe / (1000 * 2)) ** 2

        csv_file = pd.read_csv(input_file, sep=";")
        self.inflow = csv_file["Qin"]
        self.evapotranspiration_max = csv_file["ET"]
        self.rain_inflow = csv_file["Qrain"]



class PondingZone:
    def __init__(self, setup_file):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Ab = float(setup['PONDING_ZONE']['Ap'])
        self.Hover = float(setup['PONDING_ZONE']['Hover'])
        self.kWeir = float(setup['PONDING_ZONE']['Kweir'])
        self.wWeir = float(setup['PONDING_ZONE']['wWeir'])
        self.expWeir = float(setup['PONDING_ZONE']['expWeir'])
        self.Cs = float(setup['PONDING_ZONE']['Cs'])
        self.Pp = float(setup['PONDING_ZONE']['Pp'])
        self.flagp = float(setup['PONDING_ZONE']['flagp'])
        self.k_denit = float(setup['DENITRIFICATION']['k_denit_pz'])
        self.height = []
        self.height_now = 0
        self.height_after = []
        self.height_after_now = 0
        self.height_before = 0
        self.overflow = []
        self.infiltration_to_surround = []
        self.infiltration_to_filter_material = []
        self.evapotranspiration_overall = []
        self.evapotranspiration = []

    def f_concentration(self, time, GP, pollutant, threshold = 0.00002):
        concentration_pz = (pollutant.concentration_pz_before * self.height_before * self.Ab + (pollutant.concentration_inflow[time] * GP.inflow[time] - pollutant.concentration_pz_before * (self.infiltration_to_filter_material[time] + self.overflow[time]) + pollutant.reaction_rate_pz_now * self.height_now * self.Ab) * GP.dt) / (self.height_now * self.Ab)
        if concentration_pz < threshold:
            concentration_pz = 0
        return concentration_pz

    def f_evapotranspiration_overall(self, time, USZ, GP):
        if USZ.wilting_point_estimated_after[time] <= USZ.sh:
            evapotranspiration = 0.0
        elif USZ.wilting_point_estimated_after[time] <= USZ.sw:
            evapotranspiration = USZ.A * GP.evapotranspiration_max[time] * GP.Kc * (USZ.wilting_point_estimated_after[time] - USZ.sh) / (USZ.sw - USZ.sh)
        elif USZ.wilting_point_estimated_after[time] <= USZ.ss:
            evapotranspiration = USZ.A * GP.evapotranspiration_max[time] * GP.Kc * (USZ.wilting_point_estimated_after[time] - USZ.sw) / (USZ.ss - USZ.sw)
        else:
            evapotranspiration = USZ.A * GP.evapotranspiration_max[time] * GP.Kc

        evapotranspiration = evapotranspiration / (GP.dt * 1000)
        return evapotranspiration
    
    def f_evapotranspiration(self, time, USZ, SZ):
        evapotranspiration = self.evapotranspiration_overall[time] * (USZ.wilting_point_estimated[time] * USZ.porosity_now * USZ.height_now) / (USZ.wilting_point_estimated[time] * USZ.porosity_now * USZ.height_now + SZ.porosity_now * SZ.height_now)
        return evapotranspiration

    def f_weir_overflow(self, time, GP):
        volume = self.height_after_now * self.Ab + GP.dt * (GP.inflow[time] + GP.rain_inflow[time])
        if volume > self.Hover * self.Ab:
            height = volume / self.Ab
            weir_overflow = min((height - self.Hover) * self.Ab / GP.dt, self.kWeir * (height - self.Hover) ** self.expWeir)
        else:
            weir_overflow = 0
        return weir_overflow

    def f_infiltration_to_surround(self, time, USZ):
        if self.flagp == 1:
            infiltration = 0
        else:
            infiltration = USZ.Kf * ((self.Ab - USZ.A) + self.Cs * self.Pp * self.height[time])
        return infiltration

    def f_infiltration_to_filter_material(self, time, USZ, GP):
        infiltration = min(USZ.Ks * USZ.A * (self.height[time] + USZ.height_now) / USZ.height_now, self.height[time] * self.Ab / GP.dt - self.infiltration_to_surround[time], (1.0 - USZ.wilting_point_moisture_now) * USZ.porosity_now * USZ.height_now * USZ.A / GP.dt)
        return infiltration

    def f_height(self, time, GP):
        height = max(self.height_after_now + GP.dt / self.Ab * (GP.rain_inflow[time] + GP.inflow[time] - self.overflow[time]), 0)
        return height
    
    def f_height_after(self, time, GP):
        height_after = max(self.height[time] - GP.dt / self.Ab * (self.infiltration_to_filter_material[time] + self.infiltration_to_surround[time]), 0)
        return height_after


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
        self.unit_flux = []

        self.height = []
        self.height_now = self.husz_ini
        self.height_before = self.husz_ini
        self.porosity = []
        self.porosity_now = self.nusz_ini
        self.porosity_before = self.nusz_ini
        self.wilting_point_moisture = []
        self.wilting_point_moisture_now = self.sw
        self.wilting_point_moisture_before = self.sw
        self.wilting_point_estimated = []
        self.capillary_rise = []
        self.infiltration_to_sz = []
        self.wilting_point_estimated_after = []
        self.evapotranspiration = []
        self.theta = []
        self.theta_after = 0

    def f_capillary_rise(self, time, GP):
        wilting_point = self.wilting_point_estimated[time]
        den = self.sfc - self.ss
        if den == 0:
            den = 0.000001
        capillary = 4 * GP.evapotranspiration_max[time] * GP.Kc / (2.5 * den ** 2)
        if self.ss <= wilting_point <= self.sfc:
            capillary_rise = self.A * capillary * (wilting_point - self.ss) * (self.sfc - wilting_point)
        else:
            capillary_rise = 0
        return capillary_rise

    def f_infiltration_to_sz(self, time, PZ, GP):
        if self.wilting_point_estimated[time] >= self.sfc:
            infiltration_to_sz = min((self.A * self.Ks * (PZ.height_after_now + self.height_now) / self.height_now) * self.wilting_point_estimated[time] ** self.gama, (self.wilting_point_estimated[time] - self.sfc) * self.porosity_now * self.A * self.height_now / GP.dt)
        else:
            infiltration_to_sz = 0
        return infiltration_to_sz

    def f_porosity(self, GP, SZ):
        if SZ.height_now < GP.Dg:
            porosity = (self.nusz_ini * GP.Df + GP.ng * (GP.Dg - SZ.height_now)) / self.height_now
        else:
            porosity = self.nusz_ini
        return porosity
    
    def f_wilting_point_moisture_estimation(self, time, PZ, GP):
        wilting_point_estimated = max(min(self.wilting_point_moisture_now + PZ.infiltration_to_filter_material[time] * GP.dt / (self.porosity_now * self.A * self.height_now), 1), 0)
        return wilting_point_estimated
    
    def f_wilting_point_moisture_next_interaction_estimation(self, time, SZ):
        wilting_poins_estimated_next = (self.wilting_point_estimated[time] * self.porosity_now * self.height_now + SZ.porosity_now * SZ.height_now) / (self.porosity_now * self.height_now + SZ.porosity_now * SZ.height_now)
        return wilting_poins_estimated_next
    
    def f_wilting_point_moisture(self, time, GP, PZ):
        wilting_point = max(min(1.0, (self.wilting_point_moisture_before * self.height_before * self.porosity_before * self.A + GP.dt * (
                PZ.infiltration_to_filter_material[time] + self.capillary_rise[time] - self.infiltration_to_sz[time] -
                PZ.evapotranspiration[time])) / (self.A * self.height_now * self.porosity_now)), self.sh)
        return wilting_point
    
    def f_evapotranspiration(self, time, PZ):
        evapotranspiration = PZ.evapotranspiration_overall[time] - PZ.evapotranspiration[time]
        return evapotranspiration

    def f_height(self, GP, SZ):
        height = GP.L - SZ.height_now
        return height

    def f_alfa_beta(self, l):
        alfa = (self.m_usz - 1 - l) / (self.m_usz - 1)
        beta = l / (self.m_usz - 1)
        return alfa, beta

    def f_unit_flux(self, time, usz_layer, GP, PZ, SZ):
        alfa = (self.m_usz - 1 - usz_layer) / (self.m_usz - 1)
        beta = usz_layer / (self.m_usz - 1)

        if GP.hpipe > 0:
            unit_flux = (alfa * (PZ.infiltration_to_filter_material[time] - PZ.evapotranspiration[time]) + beta * (self.infiltration_to_sz[time] - self.capillary_rise[time])) / (PZ.Ab * self.theta[time])

        else:
            unit_flux = (alfa * (PZ.infiltration_to_filter_material[time] - PZ.evapotranspiration[time]) + beta * (SZ.pipe_outflow_now + SZ.infiltration_to_surround[time] - self.capillary_rise[time])) / (PZ.Ab * self.theta[time])

        return unit_flux

    def f_peclet(self, unit_flux_usz, D, dz):
        if D > 0:
            peclet = unit_flux_usz * dz / D
        else:
            peclet = 100

        return peclet


class SaturatedZone:
    def __init__(self, setup_file, GP, USZ):
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.Psz = float(setup['SATURATED_ZONE']['Psz'])
        self.flagsz = float(setup['SATURATED_ZONE']['flagsz'])
        self.m_sz = GP.n - USZ.m_usz
        self.unit_flux = []
        self.height = []
        self.porosity = []
        self.porosity_now = GP.ng
        self.height_estimated = []
        self.infiltration_to_surround = []
        self.pipe_outflow = []
        self.pipe_outflow_now = 0
        self.theta = []
        self.theta_after = 0
        if GP.hpipe > 0:
            self.height_now = GP.hpipe
        else:
            self.height_now = GP.dpipe / 1000 + 0.03
        
    def f_infiltration_to_surround(self, time, PZ, USZ):
        if self.flagsz == 1:  # lined
            infiltration_to_surround = 0.0
        else:
            infiltration_to_surround = USZ.Kf * (USZ.A + PZ.Cs * self.Psz * self.height_estimated[time])
        return infiltration_to_surround

    def f_underdrain_flow(self, time, GP, USZ):
        if self.height_estimated[time] <= GP.hpipe:
            underdrain_flow = 0
        else:
            underdrain_flow_max = (self.height_estimated[time] - GP.hpipe) * USZ.A * self.porosity_now / GP.dt - self.infiltration_to_surround[time]
            underdrain_flow_max = max(0, underdrain_flow_max)
            underdrain_flow_possible = GP.Cd * GP.Apipe * ((self.height_estimated[time] - GP.hpipe) * 2 * 9.81) ** 0.5
            underdrain_flow_possible = max(0, underdrain_flow_possible)
            underdrain_flow = min(underdrain_flow_max, underdrain_flow_possible)

        return underdrain_flow

    def f_porosity(self, GP):
        if GP.Dt + GP.Dg < self.height_now <= GP.L:
            porosity = (GP.ng * GP.Dg + GP.nt * GP.Dt + GP.nf * (self.height_now - GP.Dg - GP.Dt)) / self.height_now
        elif GP.Dg < self.height_now <= GP.Dg + GP.Dt:
            porosity = (GP.ng * GP.Dg + GP.nt * (self.height_now - GP.Dg)) / self.height_now
        else:
            porosity = GP.ng
        return porosity
    
    def f_height_estimation(self, time, GP, USZ):
        height_estimated = self.height_now + GP.dt * (USZ.infiltration_to_sz[time] - USZ.capillary_rise[time] - USZ.evapotranspiration[time]) / USZ.A / self.porosity_now
        return height_estimated
    
    def f_height(self, time, GP, USZ):
        height = self.height_now + GP.dt * (USZ.infiltration_to_sz[time] - USZ.capillary_rise[time] - self.infiltration_to_surround[time] - self.pipe_outflow[time] - USZ.evapotranspiration[time]) / USZ.A / self.porosity_now
        return height

    def f_alfa_beta(self, j):
        alfa2 = (self.m_sz - 1 - j) / (self.m_sz - 1)
        beta2 = j / (self.m_sz - 1)
        return alfa2, beta2

    def f_unit_flux(self, sz_layer, Qfs, Qhc, Qet_2, Qorif, Qinf_sz, theta_sz_now, Ab):
        alfa = (self.m_sz - 1 - sz_layer) / (self.m_sz - 1)
        beta = sz_layer / (self.m_sz - 1)

        UF_sz = (alfa * (Qfs - Qhc - Qet_2) + beta * (Qorif + Qinf_sz)) / (Ab * theta_sz_now)
        return UF_sz

    def f_peclet(self, UF_sz, D, dz):
        if D > 0:
            Pesz = UF_sz * dz / D
        else:
            Pesz = 100

        return Pesz


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


class Pollutant:
    def __init__(self, m_usz, m_sz):
        self.initial_concentration_usz = [0] * m_usz
        self.initial_concentration_sz = [0] * m_sz
        self.concentration_pz = []
        self.concentration_usz = [self.initial_concentration_usz]
        self.concentration_soil_usz = [self.initial_concentration_usz]
        self.concentration_sz = [self.initial_concentration_sz]
        self.concentration_soil_sz = [self.initial_concentration_sz]
        self.reaction_rate_usz = [self.initial_concentration_usz]
        self.reaction_rate_sz = [self.initial_concentration_sz]
        self.concentration_pz_before = 0
        self.concentration_soil_usz_before = 0
        self.concentration_soil_sz_before = 0
        self.mass_stormwater = []
        self.mass_soil = []
        self.mass_accumulated_reaction = []
        self.mass_accumulated_inflow = []
        self.mass_accumulated_overflow = []
        self.mass_accumulated_pipe_outflow = []
        self.mass_accumulated_infiltrated_to_sz = []
        self.mass_accumulated_evapotranspiration = []
        self.mass_pz = []
        self.mass_balance = []


    def f_transport(self, teta_i, teta_iplus1, ci, cs_i, dc, dc_dz, kads, kdes, D, UF, Rx, ro, f, dt, dz):
        if teta_i == 0:
            delta_c_i1 = 0
        elif teta_iplus1 == 0:
            delta_c_i1 = 0
        else:
            delta_c_i1 = ((1 / teta_iplus1) * dt * (
                    -teta_i * kads * ci + ro * kdes * cs_i + teta_i * (
                        D * f * (dc / dz ** 2) - UF * dc_dz) + Rx))
            # delta_c_i1 = ((1/teta_i)*GP.dt*(-teta_i*kads*ci + ro*kdes*cs_i + teta_i*(D*SOIL_PLANT.f*(dc/GP.dz**2) - UF*dc_dz) + Rx))
        return delta_c_i1

    def f_concentration_soil(self, cs_a, teta, kads, ci, kdes, kmicro, ro, dt, threshold=0.00000000000001):
        # Rxs = kmicro*cs_a
        Rxs = 0

        # Rxs = Um*(teta*cs_a/(Km + teta*cs_a))
        cs_abs = cs_a + ((teta / ro) * kads * ci - kdes * cs_a - Rxs) * dt

        if cs_abs <= 0:
            cs = 0
        else:
            cs = cs_abs

        if cs < threshold:
            cs = 0
        return cs

    def f_reaction_conversion(self, GP, USZ):
        reaction_converted = self.reaction_rate_usz_now * (1 / USZ.theta_after) * GP.dt
        return reaction_converted

    def f_delta_concentration_layer_usz(self, usz_layer, dz, m_usz):
        if self.peclet <= 2:
            if usz_layer == 0:  # first cell
                dc = self.concentration_usz_next_layer - 2 * self.concentration_usz_layers[
                    usz_layer] + self.concentration_pz_now
                dc_dz = (self.concentration_usz_next_layer - self.concentration_pz_now) / (2 * dz)

            elif usz_layer == (m_usz - 1):  # last cell
                dc = self.concentration_usz_layers[usz_layer] - 2 * self.concentration_usz_layers[usz_layer] + \
                     self.concentration_usz_layers[usz_layer - 1]
                dc_dz = (self.concentration_usz_layers[usz_layer] - self.concentration_usz_layers[
                    usz_layer - 1]) / dz

            else:
                dc = self.concentration_usz_next_layer - 2 * self.concentration_usz_layers[usz_layer] + \
                     self.concentration_usz_layers[usz_layer - 1]
                dc_dz = (self.concentration_usz_next_layer - self.concentration_usz_layers[usz_layer - 1]) / (
                        2 * dz)

        else:  # Peusz > 2
            if usz_layer == 0:  # first cell
                dc = self.concentration_usz_next_layer - 2 * self.concentration_usz_layers[
                    usz_layer] + self.concentration_pz_now
                dc_dz = (self.concentration_usz_layers[usz_layer] - self.concentration_pz_now) / dz

            elif usz_layer == (m_usz - 1):  # last cell
                dc = self.concentration_usz_layers[usz_layer] - 2 * self.concentration_usz_layers[usz_layer] + \
                     self.concentration_usz_layers[usz_layer - 1]
                dc_dz = (self.concentration_usz_layers[usz_layer] - self.concentration_usz_layers[
                    usz_layer - 1]) / dz

            else:
                dc = self.concentration_usz_next_layer - 2 * self.concentration_usz_layers[usz_layer] + \
                     self.concentration_usz_layers[usz_layer - 1]
                dc_dz = (self.concentration_usz_layers[usz_layer] - self.concentration_usz_layers[
                    usz_layer - 1]) / dz

        return dc, dc_dz
    
    def f_delta_concentration_layer_sz(self, sz_layer, dz, m_usz, m_sz, n):
        if m_usz < (n - 1):
            if self.peclet <= 2:
                if sz_layer == 0:  # first cell
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_usz_layers[m_usz - 1]
                    dc_dz = (self.concentration_sz_next_layer - self.concentration_usz_layers[m_usz - 1]) / (
                                2 * dz)

                elif sz_layer == (m_sz - 1):  # last cell
                    dc = self.concentration_sz_layers[sz_layer] - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz

                else:
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_next_layer - self.concentration_sz_layers[sz_layer - 1]) / (
                                2 * dz)

            else:
                if sz_layer == 0:
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_usz_layers[m_usz - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_usz_layers[
                        m_usz - 1]) / dz

                elif sz_layer == (m_sz - 1):  # last cell
                    dc = self.concentration_sz_layers[sz_layer] - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz

                else:
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz

        if m_usz == (n - 1):
            dc = self.concentration_sz_layers[sz_layer] - 2 * self.concentration_sz_layers[sz_layer] + \
                     self.concentration_sz_layers[sz_layer - 1]
            dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[sz_layer - 1]) / (
                        2 * dz)

        if m_usz == 0:
            if self.peclet <= 2:
                if sz_layer == 0:  # first cell
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[
                        sz_layer] + self.concentration_pz_now
                    dc_dz = (self.concentration_sz_next_layer - self.concentration_pz_now) / (
                                2 * dz)

                elif sz_layer == (m_sz - 1):  # last cell
                    dc = self.concentration_sz_layers[sz_layer] - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz

                else:
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_next_layer - self.concentration_sz_layers[sz_layer - 1]) / (
                                2 * dz)

            else:
                if sz_layer == 0:  # first cell
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[
                        sz_layer] + self.concentration_pz_now
                    dc_dz = (self.concentration_sz_layers[
                                     sz_layer] - self.concentration_pz_now) / dz

                elif sz_layer == (m_sz - 1):  # last cell
                    dc = self.concentration_sz_layers[sz_layer] - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz

                else:
                    dc = self.concentration_sz_next_layer - 2 * self.concentration_sz_layers[sz_layer] + \
                             self.concentration_sz_layers[sz_layer - 1]
                    dc_dz = (self.concentration_sz_layers[sz_layer] - self.concentration_sz_layers[
                        sz_layer - 1]) / dz
        return dc, dc_dz        

    def f_delta_concentration_usz(self, time, usz_layer, m_usz, tteta_usz, theta_usz_after, unit_flux_now, ro, f, dt, dz, threshold=0.0000000000000001):
        dc, dc_dz = self.f_delta_concentration_layer_usz(usz_layer, dz, m_usz)


        delta_concentration = self.f_transport(tteta_usz[time], theta_usz_after, self.concentration_usz_layers[usz_layer],
                                      self.concentration_soil_usz_layer, dc, dc_dz, self.kads, self.kdes,
                                      self.D, unit_flux_now, self.reaction_rate_usz_now, ro, f,
                                      dt, dz)

        if theta_usz_after > 0:
            concentration_now = self.concentration_usz_layers[usz_layer] + delta_concentration
        else:
            concentration_now = 0

        if concentration_now <= threshold:
            concentration_now = 0
        return concentration_now

    def f_delta_concentration_sz(self, time, sz_layer, m_usz, m_sz, tteta_sz, theta_sz_after, unit_flux_now, ro, f, dt, dz, n, threshold=0.0000000000000001):
        dc, dc_dz = self.f_delta_concentration_layer_sz(sz_layer, dz, m_usz, m_sz, n)
        delta_c_doc = self.f_transport(tteta_sz[time], theta_sz_after, self.concentration_sz_layers[sz_layer],
                                      self.concentration_soil_sz_layer, dc, dc_dz, self.kads2, self.kdes2,
                                      self.D, unit_flux_now, self.reaction_rate_sz_now, ro, f,
                                      dt, dz)
        if theta_sz_after > 0:
            concentration = self.concentration_sz_layers[sz_layer] + delta_c_doc
        else:
            concentration = 0

        if concentration <= threshold:
            concentration = 0
        return concentration

    def f_mass_stormwater(self, time, m_usz, m_sz, Ab, tteta_usz, thusz, tteta_sz, thsz, hpipe):
        mass_stormwater_usz = sum(self.concentration_usz[time]) * Ab * tteta_usz[time] * thusz[time] * 1000 / m_usz
        if hpipe > 0:
            mass_stormwater_sz = sum(self.concentration_sz[time]) * Ab * tteta_sz[time] * thsz[time] * 1000 / m_sz
        else:
            mass_stormwater_sz = 0
        mass_stormwater = mass_stormwater_usz + mass_stormwater_sz
        return mass_stormwater

    def f_mass_soil(self, time, m_usz, m_sz, thusz, thsz, Ab, ro, hpipe):
        mass_soil_usz_before = self.concentration_soil_usz_before * ro * Ab * thusz[time] * 1000
        mass_soil_usz_after = sum(self.concentration_soil_usz[time]) * ro * Ab * thusz[time] * 1000 / m_usz

        if hpipe > 0:
            mass_soil_sz_before = self.concentration_soil_sz_before * ro * Ab * thsz[time] * 1000
            mass_soil_sz_after = sum(self.concentration_soil_sz[time]) * ro * Ab * thsz[time] * 1000 / m_sz
        else:
            mass_soil_sz_before = 0
            mass_soil_sz_after = 0

        mass_soil_before = mass_soil_usz_before + mass_soil_sz_before
        mass_soil_after = mass_soil_usz_after + mass_soil_sz_after

        return mass_soil_after - mass_soil_before

    def f_mass_reaction_rate(self, time, m_usz, m_sz, tteta_usz, tteta_sz, thusz, thsz, Ab, hpipe):
        mass_reaction_rate_usz = sum(self.reaction_rate_usz[time]) * Ab * tteta_usz[time] * thusz[time] * 1000 / m_usz
        if hpipe > 0:
            mass_reaction_rate_sz = sum(self.reaction_rate_sz[time]) * Ab * tteta_sz[time] * thsz[time] * 1000 / m_sz
        else:
            mass_reaction_rate_sz = 0

        mass_reaction_rate = -(mass_reaction_rate_usz + mass_reaction_rate_sz)

        if time != 0:
            mass_reaction_rate += self.mass_accumulated_reaction[-1]
        return mass_reaction_rate

    def f_mass_inflow(self, time, tQin, dt):
        mass_inflow = tQin[time] * self.concentration_inflow[time] * dt * 1000
        if time != 0:
            mass_inflow += self.mass_accumulated_inflow[-1]
        return mass_inflow

    def f_mass_overflow(self, time, tQover, dt):
        mass_overflow = tQover[time] * self.concentration_pz[time] * dt * 1000
        if time != 0:
            mass_overflow += self.mass_accumulated_overflow[-1]
        return mass_overflow

    def f_mass_pipe_outflow(self, time, m_usz, m_sz, tQpipe, dt, hpipe):
        if hpipe > 0:
            mass_pipe_outflow = tQpipe[time] * self.concentration_sz[time][m_sz - 1] * dt * 1000
        else:
            mass_pipe_outflow = tQpipe[time] * self.concentration_usz[time][m_usz - 1] * dt * 1000

        if time != 0:
            mass_pipe_outflow += self.mass_accumulated_pipe_outflow[-1]

        return mass_pipe_outflow

    def f_mass_infiltration_to_sz(self, time, m_usz, m_sz, tQinfsz, dt, hpipe):
        if hpipe > 0:
            mass_infiltration_to_sz = tQinfsz[time] * self.concentration_sz[time][m_sz - 1] * dt * 1000
        else:
            mass_infiltration_to_sz = tQinfsz[time] * self.concentration_usz[time][m_usz - 1] * dt * 1000

        if time != 0:
            mass_infiltration_to_sz += self.mass_accumulated_infiltrated_to_sz[-1]

        return mass_infiltration_to_sz

    def f_mass_evapotranspiration(self, time, tQet, dt):
        mass_evapotranspiration = tQet[time] * self.concentration_usz_layers_now[0] * dt * 1000

        if time != 0:
            mass_evapotranspiration += self.mass_accumulated_evapotranspiration[-1]

        return mass_evapotranspiration

    def f_mass_pz(self, time, thpEND, Ab):
        mass_pz = thpEND[time] * Ab * 1000 * self.concentration_pz[time]
        return mass_pz
    
    def f_mass_balance_stormwater(self, time, USZ, SZ, WFR, PZ, GP, SOIL_PLANT):
        self.mass_soil.append(self.f_mass_soil(time, USZ.m_usz, SZ.m_sz, USZ.height, SZ.height, PZ.Ab, SOIL_PLANT.ro, GP.hpipe))
        self.mass_accumulated_reaction.append(self.f_mass_reaction_rate(time, USZ.m_usz, SZ.m_sz, USZ.theta, SZ.theta, USZ.height, SZ.height, PZ.Ab, GP.hpipe))
        self.mass_accumulated_inflow.append(self.f_mass_inflow(time, GP.inflow, GP.dt))
        self.mass_accumulated_overflow.append(self.f_mass_overflow(time, PZ.overflow, GP.dt))
        self.mass_accumulated_pipe_outflow.append(self.f_mass_pipe_outflow(time, USZ.m_usz, SZ.m_sz, SZ.pipe_outflow, GP.dt, GP.hpipe))
        self.mass_accumulated_infiltrated_to_sz.append(self.f_mass_infiltration_to_sz(time, USZ.m_usz, SZ.m_sz, SZ.infiltration_to_surround, GP.dt, GP.hpipe))
        self.mass_accumulated_evapotranspiration.append(self.f_mass_evapotranspiration(time, PZ.evapotranspiration_overall, GP.dt))
        self.mass_pz.append(self.f_mass_pz(time, PZ.height_after, PZ.Ab))
        mass_balance_stormwater = self.mass_accumulated_inflow[-1] - self.mass_pz[-1] - self.mass_accumulated_overflow[-1] - self.mass_accumulated_pipe_outflow[-1] - self.mass_accumulated_infiltrated_to_sz[-1] - self.mass_accumulated_evapotranspiration[-1] - self.mass_soil[-1] - self.mass_accumulated_reaction[-1]
        return mass_balance_stormwater

    def f_mass_balance_concentration(self, time, m_usz, Ab, tteta_usz, thusz):
        concentration_delta = (self.mass_balance[-1] - self.mass_stormwater_now) / (Ab * tteta_usz[time] * thusz[time] * 1000 / m_usz)
        self.concentration_usz_layers_now[1] = self.concentration_usz_layers_now[1] + concentration_delta
        if self.concentration_usz_layers_now[1] < 0:
            self.concentration_usz_layers_now[1] = 0

    def water_quality_results(self, m_usz, m_sz):
        columns_name = ["usz" + str(num) for num in range(m_usz)]
        columns_name += ["sz" + str(num) for num in range(m_sz)]
        if len(self.concentration_soil_usz) != 0:
            columns_name += ["usz_soil" + str(num) for num in range(m_usz)]
        if len(self.concentration_soil_sz) != 0:
            columns_name += ["sz_soil" + str(num) for num in range(m_sz)]
        columns_name += ["usz_rx" + str(num) for num in range(m_usz)]
        columns_name += ["sz_rx" + str(num) for num in range(m_sz)]
        df_usz = pd.DataFrame(self.concentration_usz)
        df_sz = pd.DataFrame(self.concentration_sz)
        df_soil_usz = pd.DataFrame(self.concentration_soil_usz)
        df_soil_sz = pd.DataFrame(self.concentration_soil_sz)
        df_rx_usz = pd.DataFrame(self.reaction_rate_usz)
        df_rx_sz = pd.DataFrame(self.reaction_rate_sz)
        frames = [df_usz, df_sz, df_soil_usz, df_soil_sz, df_rx_usz, df_rx_sz]
        df = pd.concat(frames, axis=1)
        df.columns = columns_name
        self.concentration_pz.append(0)
        df['pz'] = self.concentration_pz
        df['c_in'] = self.concentration_inflow
        df['t'] = list(range(len(self.concentration_usz)))
        return df


class Ammonia(Pollutant):
    def __init__(self, m_usz, m_sz, setup_file, inflow_file):
        super(Ammonia, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D = float(setup['NH4']['D_nh4'])
        self.kads = float(setup['NH4']['kads_nh4'])
        self.kdes = float(setup['NH4']['kdes_nh4'])
        self.kads2 = float(setup['NH4']['kads2_nh4'])
        self.kdes2 = float(setup['NH4']['kdes2_nh4'])
        self.k_mb = float(setup['NH4']['k_nh4_mb'])
        self.Fm = float(setup['NH4']['Fm_nh4'])
        self.Km = float(setup['NH4']['Km_nh4'])
        csv_file = pd.read_csv(inflow_file, sep=';')
        self.concentration_inflow = csv_file['nh4'].tolist()

    def f_reaction_pz(self):
        return 0

    def f_reaction_usz(self, usz_layer, GP):
        reaction_rate = -GP.k_nit * self.concentration_usz_layers[usz_layer]
        return reaction_rate

    def f_reaction_sz(self):
        return 0

    def f_plant_uptake_usz(self, time, usz_layer, USZ, SOIL_PLANT):
        plant_uptake = -SOIL_PLANT.root_fraction * (self.Fm * USZ.theta[time] * self.concentration_usz_layers[usz_layer] / (self.Km + USZ.theta[time] * self.concentration_usz_layers[usz_layer]))
        return plant_uptake

    def f_plant_uptake_sz(self, C_nh4_3, theta_sz, root_fraction):
        PU_nh4_3 = -root_fraction * (self.Fm * theta_sz * C_nh4_3 / (self.Km + theta_sz * C_nh4_3))
        return PU_nh4_3


class Nitrate(Pollutant):
    def __init__(self, m_usz, m_sz, setup_file, inflow_file):
        super(Nitrate, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D = float(setup['NO3']['D_no3'])
        self.Fm = float(setup['NO3']['Fm_no3'])
        self.Km = float(setup['NO3']['Km_no3'])
        self.kads = 0
        self.kdes = 0
        self.kads2 = 0
        self.kdes2 = 0
        csv_file = pd.read_csv(inflow_file, sep=';')
        self.concentration_inflow = csv_file['no3'].tolist()

    def f_reaction_pz(self):
        return 0

    def f_reaction_usz(self, usz_layer, GP, NH4):
        reaction_rate = GP.k_nit * NH4.concentration_usz_layers[usz_layer]
        return reaction_rate

    def f_reaction_sz(self, C_no3_iminus1, C_o2_i, C_doc_iminus1, k_denit):
        #     Of = O2.K/(O2.K+C_o2_i)
        #     bDOCf = (C_doc_iminus1 + DOC.bDOCd*GP.dt)/(C_doc_iminus1 + DOC.bDOCd*GP.dt + DOC.KbDOC)
        #
        #     k2 = GP.k_denit*Of*bDOCf
        k2 = k_denit  ###testando sem influencia de DOC e O2
        R_denit = - k2 * C_no3_iminus1
        return R_denit

    def f_plant_uptake_usz(self, time, usz_layer, USZ, SOIL_PLANT):
        plant_uptake = -SOIL_PLANT.root_fraction * (self.Fm * USZ.theta[time] * self.concentration_usz_layers[usz_layer] / (self.Km + USZ.theta[time] * self.concentration_usz_layers[usz_layer]))
        return plant_uptake

    def f_plant_uptake_sz(self, C_no3_3, theta_sz, root_fraction):
        PU_no3_3 = -root_fraction * (self.Fm * theta_sz * C_no3_3 / (self.Km + theta_sz * C_no3_3))

        return PU_no3_3

    def f_concentration_soil(self):
        return 0

    def f_mass_soil(self):
        return 0

    def f_mass_balance_stormwater(self, time, USZ, SZ, WFR, PZ, GP):
        self.mass_soil.append(self.f_mass_soil())
        self.mass_accumulated_reaction.append(self.f_mass_reaction_rate(time, USZ.m_usz, SZ.m_sz, USZ.theta, SZ.theta, USZ.height, SZ.height, PZ.Ab, GP.hpipe))
        self.mass_accumulated_inflow.append(self.f_mass_inflow(time, GP.inflow, GP.dt))
        self.mass_accumulated_overflow.append(self.f_mass_overflow(time, PZ.overflow, GP.dt))
        self.mass_accumulated_pipe_outflow.append(self.f_mass_pipe_outflow(time, USZ.m_usz, SZ.m_sz, SZ.pipe_outflow, GP.dt, GP.hpipe))
        self.mass_accumulated_infiltrated_to_sz.append(self.f_mass_infiltration_to_sz(time, USZ.m_usz, SZ.m_sz, SZ.infiltration_to_surround, GP.dt, GP.hpipe))
        self.mass_accumulated_evapotranspiration.append(self.f_mass_evapotranspiration(time, PZ.evapotranspiration_overall, GP.dt))
        self.mass_pz.append(self.f_mass_pz(time, PZ.height_after, PZ.Ab))
        mass_balance_stormwater = self.mass_accumulated_inflow[-1] - self.mass_pz[-1] - self.mass_accumulated_overflow[-1] - self.mass_accumulated_pipe_outflow[-1] - self.mass_accumulated_infiltrated_to_sz[-1] - self.mass_accumulated_evapotranspiration[-1] - self.mass_soil[-1] - self.mass_accumulated_reaction[-1]
        return mass_balance_stormwater

class Oxygen(Pollutant):
    def __init__(self, m_usz, m_sz, setup_file, inflow_file):
        super(Oxygen, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D = float(setup['O2']['D_o2'])
        self.K = float(setup['O2']['k_inib_o2'])  # perguntar pq K no lugar de k_inib_02
        self.k = float(setup['O2']['k_o2'])
        self.kads = 0
        self.kdes = 0
        self.kads2 = 0
        self.kdes2 = 0
        csv_file = pd.read_csv(inflow_file, sep=';')
        self.concentration_inflow = csv_file['o2'].tolist()
        
    def f_reaction_pz(self):
        return 0

    def f_reaction_usz(self, usz_layer, GP, NH4):
        reaction_rate = -self.k * self.concentration_usz_layers[usz_layer] - GP.k_nit * NH4.concentration_usz_layers[usz_layer] / 2
        return reaction_rate

    def f_reaction_sz(self, C_o2_iminus1, C_nh4_iminus1, k_nit):
        R_o2 = -self.k * C_o2_iminus1 - k_nit * C_nh4_iminus1 / 2

        return R_o2

    def f_plant_uptake_usz(self, time, usz_layer, USZ, SOIL_PLANT):
        plant_uptake = -SOIL_PLANT.root_fraction * (SOIL_PLANT.lamda * (USZ.theta[time] * SOIL_PLANT.c_o2_root - USZ.theta[time] * self.concentration_usz_layers[usz_layer]))
        return plant_uptake

    def f_plant_uptake_sz(self, C_o2_3, C_o2_root, theta_sz, root_fraction, lamda):
        PU_o2_3 = -root_fraction * (lamda * (theta_sz * C_o2_root - theta_sz * C_o2_3))
        return PU_o2_3

    def f_concentration_soil(self):
        return 0

    def f_mass_soil(self):
        return 0
    
    def f_mass_balance_stormwater(self, time, USZ, SZ, WFR, PZ, GP):
        self.mass_soil.append(self.f_mass_soil())
        self.mass_accumulated_reaction.append(self.f_mass_reaction_rate(time, USZ.m_usz, SZ.m_sz, USZ.theta, SZ.theta, USZ.height, SZ.height, PZ.Ab, GP.hpipe))
        self.mass_accumulated_inflow.append(self.f_mass_inflow(time, GP.inflow, GP.dt))
        self.mass_accumulated_overflow.append(self.f_mass_overflow(time, PZ.overflow, GP.dt))
        self.mass_accumulated_pipe_outflow.append(self.f_mass_pipe_outflow(time, USZ.m_usz, SZ.m_sz, SZ.pipe_outflow, GP.dt, GP.hpipe))
        self.mass_accumulated_infiltrated_to_sz.append(self.f_mass_infiltration_to_sz(time, USZ.m_usz, SZ.m_sz, SZ.infiltration_to_surround, GP.dt, GP.hpipe))
        self.mass_accumulated_evapotranspiration.append(self.f_mass_evapotranspiration(time, PZ.evapotranspiration_overall, GP.dt))
        self.mass_pz.append(self.f_mass_pz(time, PZ.height_after, PZ.Ab))
        mass_balance_stormwater = self.mass_accumulated_inflow[-1] - self.mass_pz[-1] - self.mass_accumulated_overflow[-1] - self.mass_accumulated_pipe_outflow[-1] - self.mass_accumulated_infiltrated_to_sz[-1] - self.mass_accumulated_evapotranspiration[-1] - self.mass_soil[-1] - self.mass_accumulated_reaction[-1]
        return mass_balance_stormwater

class DissolvedOrganicCarbon(Pollutant):
    def __init__(self, m_usz, m_sz, setup_file, inflow_file):
        super(DissolvedOrganicCarbon, self).__init__(m_usz, m_sz)
        setup = configparser.ConfigParser()
        setup.read(setup_file)
        self.D = float(setup['DOC']['D_doc'])
        self.fb = float(setup['DOC']['fb_doc'])
        self.bDOCd = float(setup['DOC']['bDOCd'])
        self.KbDOC = float(setup['DOC']['KbDOC'])
        self.k = float(setup['DOC']['k_doc'])
        self.kads = float(setup['DOC']['kads_doc'])
        self.kdes = float(setup['DOC']['kdes_doc'])
        self.kads2 = float(setup['DOC']['kads2_doc'])
        self.kdes2 = float(setup['DOC']['kdes2_doc'])
        self.k_mb = float(setup['DOC']['k_doc_mb'])
        csv_file = pd.read_csv(inflow_file, sep=';')
        self.concentration_inflow = csv_file['doc'].tolist()
        
    def f_reaction_pz(self):
        return 0

    def f_reaction_usz(self, usz_layer):
        reaction_rate = -self.k * self.concentration_usz_layers[usz_layer] + self.bDOCd
        return reaction_rate

    def f_reaction_sz(self, C_doc_iminus1):
        R_doc = -self.k * C_doc_iminus1 + self.bDOCd
        return R_doc