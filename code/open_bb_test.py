from openbb import obb
output = obb.equity.price.historical(".SPX")
df = output.to_dataframe()