import win32com.client as win32

BKP = r"C:\Users\boate\distillation-surrogate\column.bkp"
FEED = r"\Data\Streams\S1\Input"
BLK = r"\Data\Blocks\B1"

F, z = 100.0, 0.5
D = 47.98
R_values = [1.744, 1.745, 1.75]

aspen = win32.Dispatch("Apwn.Document")
aspen.InitFromArchive2(BKP)
aspen.SuppressDialogs = 1
aspen.Visible = False

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

try:
    put(FEED + r"\TOTFLOW\MIXED", F)
    put(FEED + r"\FLOW\MIXED\BENZENE", z)
    put(FEED + r"\FLOW\MIXED\TOLUENE", 1.0 - z)
    put(BLK + r"\Input\BASIS_D", D)

    print("R      duty_kW    xD       recovery")
    for R in R_values:
        put(BLK + r"\Input\BASIS_RR", R)
        aspen.Engine.Run2()
        duty_kW = get(BLK + r"\Output\REB_DUTY") * 4.184 / 1000
        xD = get(r"\Data\Streams\S2\Output\MOLEFRAC\MIXED\BENZENE")
        rec = D * xD / (F * z)
        print(f"{R:<6} {duty_kW:9.1f}  {xD:.5f}  {rec:.4f}")
finally:
    try:
        aspen.Close()
    except Exception:
        pass