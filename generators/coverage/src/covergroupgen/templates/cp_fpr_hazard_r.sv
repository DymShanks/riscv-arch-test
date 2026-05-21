    cp_fpr_hazard_r : coverpoint check_fpr_hazards(ins.hart, ins.issue, 1)  iff (ins.trap == 0 )  {
        //FPR RAW hazard
        bins hazards[]  = {NO_HAZARD, RAW_HAZARD};
    }
