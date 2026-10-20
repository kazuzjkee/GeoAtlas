import geopandas as gpd

path = 'Py_Geo/shape/russia/Russia.shp'

try:
    gdf = gpd.read_file(path)
    print("=== СЫРЫЕ ДАННЫЕ ФАЙЛА ===")
    print("1. CRS (какую проекцию видит Python):")
    print(gdf.crs)
    print("\n2. Границы (Xmin, Ymin, Xmax, Ymax):")
    print(gdf.total_bounds)
    print("\n3. Координаты центра первого объекта:")
    print(gdf.geometry.iloc[0].centroid.coords[0])
    print("==========================")
except Exception as e:
    print("Ошибка чтения:", e)