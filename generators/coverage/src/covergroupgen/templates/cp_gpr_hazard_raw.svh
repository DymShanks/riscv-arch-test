    cp_gpr_hazard_raw_rs1 : coverpoint (
        traceDataQ[ins.hart][ins.issue][2].valid &&
        traceDataQ[ins.hart][ins.issue][2].has_rd &&
        traceDataQ[ins.hart][ins.issue][2].rd != "x0" &&
        traceDataQ[ins.hart][ins.issue][2].rd != "zero" &&
        ins.current.has_rs1 &&
        ins.current.rs1 == traceDataQ[ins.hart][ins.issue][2].rd
    ) iff (ins.trap == 0) {
        // Depth=1 RAW: current rs1 depends on the producer at N-2.
        bins hit = {1};
    }

    cp_gpr_hazard_raw_rs2 : coverpoint (
        traceDataQ[ins.hart][ins.issue][2].valid &&
        traceDataQ[ins.hart][ins.issue][2].has_rd &&
        traceDataQ[ins.hart][ins.issue][2].rd != "x0" &&
        traceDataQ[ins.hart][ins.issue][2].rd != "zero" &&
        ins.current.has_rs2 &&
        ins.current.rs2 == traceDataQ[ins.hart][ins.issue][2].rd
    ) iff (ins.trap == 0) {
        // Depth=1 RAW: current rs2 depends on the producer at N-2.
        bins hit = {1};
    }
