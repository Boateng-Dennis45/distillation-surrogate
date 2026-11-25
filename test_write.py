import win32com.client as win32

path = r"C:\Users\boate\distillation-surrogate\column.bkp"
aspen = win32.Dispatch("Apwn.Document")
aspen.InitFromArchive2(path)
aspen.SuppressDialogs = 1
aspen.Visible = True

FEED = r"\Data\Streams\S1\Input"
BLK = r"\Data\Blocks\B1"

def get(p):
    node = aspen.Tree.FindNode(p)
    return "NOT FOUND" if node is None else node.Value

def put(p, value):
    node = aspen.Tree.FindNode(p)
    if node is None:
        raise RuntimeError("Path not found: " + p)
    node.Value = value

def show(title):
    print("---", title, "---")
    print("feed flow       ", get(FEED + r"\TOTFLOW\MIXED"))
    print("feed benzene    ", get(FEED + r"\FLOW\MIXED\BENZENE"))
    print("reflux ratio    ", get(BLK + r"\Input\BASIS_RR"))
    print("distillate rate ", get(BLK + r"\Input\BASIS_D"))
    print("reboiler duty   ", get(BLK + r"\Output\REB_DUTY"))
    print("distillate benz ", get(r"\Data\Streams\S2\Output\MOLEFRAC\MIXED\BENZENE"))

try:
    show("base case")

    put(FEED + r"\TOTFLOW\MIXED", 80.0)
    put(FEED + r"\FLOW\MIXED\BENZENE", 0.40)
    put(FEED + r"\FLOW\MIXED\TOLUENE", 0.60)
    put(BLK + r"\Input\BASIS_RR", 2.0)
    put(BLK + r"\Input\BASIS_D", 32.0)

    aspen.Engine.Run2()
    show("new case")

    print("--- run status ---")
    status = aspen.Tree.FindNode(r"\Data\Results Summary\Run-Status\Output")
    if status is None:
        print("run-status node not found")
    else:
        for child in status.Elements:
            try:
                print(child.Name, child.Value)
            except Exception:
                pass
finally:
    try:
        aspen.Close()
    except Exception:
        pass