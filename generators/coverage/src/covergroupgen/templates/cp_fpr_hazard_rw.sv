    cp_fpr_hazard_rw : coverpoint check_fpr_hazards(ins.hart, ins.issue, 1)  iff (ins.trap == 0 )  {
        //FPR hazard
        bins hazards[]  = {NO_HAZARD, RAW_HAZARD, WAW_HAZARD, WAR_HAZARD};
    }
