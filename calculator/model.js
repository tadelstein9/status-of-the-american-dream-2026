// The run-out arithmetic, line for line from arithmetic.py. The page and
// test_model.py both load this file; test_model.py checks it against the study.
(function (root) {
  "use strict";

  function acaNet(benefit, D) {
    const a = D.aca, full = a.bench40 * a.age62 / a.age40, income = benefit * 12;
    const pct = income / a.fpl * 100;
    for (const [lo, hi, s, e] of a.bands) {
      if (pct >= lo && pct < hi) return Math.min(full, (s + (pct - lo) / (hi - lo) * (e - s)) * income / 12);
    }
    return full;    // no credit below 100% of the poverty line or at 400% and above
  }

  // v: benefit, savings, rent, carPayment, carRunning, food, phone, outOfPocket, other, sex
  function run(v, D) {
    const g = D.costGrowth, planG = D.planG[v.sex === "men" ? "men" : "women"];
    const health = acaNet(v.benefit, D);
    const fixed = v.rent + v.carRunning + v.food + v.phone + v.outOfPocket + v.other;
    const medicare = m => D.medicare.partB + D.medicare.partD + planG[62 + Math.floor(m / 12)] / 12;
    const healthAt = m => m >= D.medicare.month ? medicare(m) : health;
    const carPay = m => {
      const c = D.car;
      if (m < c.loanMonths) return v.carPayment;
      if (m >= c.replaceMonth && m < c.replaceMonth + c.loanMonths)
        return v.carPayment * Math.pow(1 + g, Math.floor(c.replaceMonth / 12));
      return 0;
    };
    const monthCost = m => (fixed + healthAt(m)) * Math.pow(1 + g, Math.floor(m / 12)) + carPay(m);
    const snapParams = m => {
      const fy = Math.floor((m + 3) / 12);    // 0 = fiscal 2026 (Jan-Sep 2026)
      if (fy === 0) return D.snap.fy26;
      const k = Math.pow(1 + D.cola, fy - 1), [lim, std, mn, mx] = D.snap.fy27;
      return [lim * k, std * k, mn, mx * k];
    };
    const snap = (m, income) => {
      const grow = Math.pow(1 + g, Math.floor(m / 12)), [lim, std, mn, mx] = snapParams(m);
      const medical = Math.max(0, (healthAt(m) + v.outOfPocket) * grow - D.snap.medFloor);
      const adjusted = Math.max(0, income - std - medical);
      const shelter = Math.max(0, v.rent * grow - adjusted / 2);
      const net = Math.max(0, adjusted - shelter);
      return net > lim ? 0 : Math.max(mn, mx - 0.3 * net);
    };

    let bal = v.savings, out = null;
    const rows = [];
    for (let y = 0; y < 10; y++) {
      const b = v.benefit * Math.pow(1 + D.cola, y);
      let costs = 0, food = 0;
      for (let k = 0; k < 12; k++) { costs += monthCost(y * 12 + k); food += snap(y * 12 + k, b); }
      const gap = b * 12 + food - costs;
      bal += gap;
      if (out === null && bal < 0) out = 62 + y;
      rows.push({ age: 62 + y, benefit: b, snap: food / 12, costs: costs / 12, gap, balance: bal });
    }
    return { rows, out, health, firstGap: v.benefit - (fixed + health + v.carPayment) };
  }

  // Where the monthly check falls against each program's limit at 62, as in Figure 6.1.
  // Positive = over the limit by that much a month; negative = under.
  function programs(v, D) {
    const b = v.benefit, L = D.limits, [lim, std, mn, mx] = D.snap.fy27;
    const medical = Math.max(0, acaNet(b, D) + v.outOfPocket - D.snap.medFloor);
    const adjusted = Math.max(0, b - std - medical);
    const net = Math.max(0, adjusted - Math.max(0, v.rent - adjusted / 2));
    return {
      snap: { over: net - lim, amount: net > lim ? 0 : Math.max(mn, mx - 0.3 * net) },
      extraHelp: { over: b - 20 - L.extraHelp },
      qi: { over: b - L.qi },
      ceap: { over: (b * 12 - L.ceapYear) / 12 },
      tefap: { over: (b * 12 - L.tefapYear) / 12 },
    };
  }

  const api = { acaNet, run, programs };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RunOut = api;
})(this);
