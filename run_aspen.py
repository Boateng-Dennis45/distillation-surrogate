import csv
import time
import win32com.client as win32

BKP = r"C:\Users\boate\distillation-surrogate\column.bkp"
INPUTS = r"C:\Users\boate\distillation-surrogate\inputs.csv"
OUTPUT = r"C:\Users\boate\distillation-surrogate\results.csv"
MAX_ROWS = None       # test with 10 first; later set to None for all rows
VISIBLE = False      # set False later for faster runs

FEED = r"\Data\Streams\S1\Input"
BLK = r"\Data\Blocks\B1"
STAT = r"\Data\Results Summary\Run-Status\Output"

with open(INPUTS, newline="") as f:
    inputs = list(csv.DictReader(f))
if MAX_ROWS is not None:
    inputs = inputs[:MAX_ROWS]

aspen = win32.Dispatch("Apwn.Document")
aspen.InitFromArchive2(BKP)
aspen.SuppressDialogs = 1
aspen.Visible = VISIBLE

def get(p):
    node = aspen.Tree.FindNode(p)
    if node is None:
        raise RuntimeError("Path not found: " + p)
    return node.Value

def put(p, value):
    node = aspen.Tree.FindNode(p)
    if node is None:
        raise RuntimeError("Path not found: " + p)
    node.Value = value

rows = []

def save():
    if not rows:
        return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(OUTPUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

try:
    for i, r in enumerate(inputs):
        z = float(r["z_benzene"])
        out = {
            "feed_flow_kmolh": float(r["feed_flow_kmolh"]),
            "z_benzene": z,
            "reflux_ratio": float(r["reflux_ratio"]),
            "distillate_kmolh": float(r["distillate_kmolh"]),
        }
        t0 = time.time()
        try:
            put(FEED + r"\TOTFLOW\MIXED", out["feed_flow_kmolh"])
            put(FEED + r"\FLOW\MIXED\BENZENE", z)
            put(FEED + r"\FLOW\MIXED\TOLUENE", 1.0 - z)
            put(BLK + r"\Input\BASIS_RR", out["reflux_ratio"])
            put(BLK + r"\Input\BASIS_D", out["distillate_kmolh"])

            aspen.Engine.Run2()

            out["reboiler_duty_cal_s"] = get(BLK + r"\Output\REB_DUTY")
            out["condenser_duty_cal_s"] = get(BLK + r"\Output\COND_DUTY")
            out["xD_benzene"] = get(r"\Data\Streams\S2\Output\MOLEFRAC\MIXED\BENZENE")
            out["xB_benzene"] = get(r"\Data\Streams\S3\Output\MOLEFRAC\MIXED\BENZENE")
            for name in ["RSTAT", "SSTAT", "UOSSTAT", "UOSSTAT2", "ITSTAT"]:
                out["status_" + name] = get(STAT + "\\" + name)
            out["error"] = ""
        except Exception as e:
            out["error"] = str(e)[:150]

        out["run_seconds"] = round(time.time() - t0, 1)
        rows.append(out)
        print(i + 1, "of", len(inputs), "|", out.get("reboiler_duty_cal_s"),
              "|", out.get("xD_benzene"), "|", out["error"])

        if (i + 1) % 10 == 0:
            save()
finally:
    save()
    try:
        aspen.Close()
    except Exception:
        pass