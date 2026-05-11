    cp_fpr_hazard_w : coverpoint check_fpr_hazards(ins.hart, ins.issue)  iff (ins.trap == 0 )  {
        //FPR write hazard
        bins hazards[]  = {NO_HAZARD, WAW_HAZARD, WAR_HAZARD};
    }

