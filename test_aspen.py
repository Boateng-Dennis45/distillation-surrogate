import win32com.client as win32

path = r"C:\Users\boate\distillation-surrogate\column.bkp"

aspen = win32.Dispatch("Apwn.Document")
aspen.InitFromArchive2(path)
aspen.SuppressDialogs = 1
aspen.Visible = True

def get(node_path):
    node = aspen.Tree.FindNode(node_path)
    return "NOT FOUND" if node is None else node.Value

paths = {
    "feed flow":           r"\Data\Streams\S1\Input\TOTFLOW\MIXED",
    "feed benzene frac":   r"\Data\Streams\S1\Input\FRAC\MIXED\BENZENE",
    "reflux ratio":        r"\Data\Blocks\B1\Input\BASIS_RR",
    "distillate rate":     r"\Data\Blocks\B1\Input\BASIS_D",
    "reboiler duty":       r"\Data\Blocks\B1\Output\REB_DUTY",
    "condenser duty":      r"\Data\Blocks\B1\Output\COND_DUTY",
    "distillate benzene":  r"\Data\Streams\S2\Output\MOLEFRAC\MIXED\BENZENE",
    "bottoms benzene":     r"\Data\Streams\S3\Output\MOLEFRAC\MIXED\BENZENE",
}

print("--- before running ---")
for name, p in paths.items():
    print(name, "=", get(p))

aspen.Engine.Run2()

print("--- after running ---")
for name, p in paths.items():
    print(name, "=", get(p))

aspen.Close()
aspen.Quit()