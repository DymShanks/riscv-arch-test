    cp_gpr_hazard_r : coverpoint check_gpr_hazards(ins.hart, ins.issue, 1)  iff (ins.trap == 0 )  {
        bins no_hazard  = {NO_HAZARD};
        bins raw_hazard = {RAW_HAZARD};
    }
