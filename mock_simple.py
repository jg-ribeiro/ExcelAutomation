import win32com.client as win32

def listar_conexoes_em_refresh(workbook):
    conexoes = []

    try:
        total = workbook.Connections.Count
    except Exception as e:
        print('Nâo foi possível acessar as conexões do workbook:', e)
        return conexoes  # retorna lista vazia

    for i in range(1, total + 1):
        try:
            conn = workbook.Connections.Item(i)

            if hasattr(conn, "Refreshing") and conn.Refreshing:
                conexoes.append(conn.Name)
                continue

            if hasattr(conn, "OLEDBConnection"):
                if conn.OLEDBConnection.Refreshing:
                    conexoes.append(conn.Name)
                    continue

            if hasattr(conn, "ODBCConnection"):
                if conn.ODBCConnection.Refreshing:
                    conexoes.append(conn.Name)
                    continue

        except Exception:
            continue

    return conexoes


excel = win32.DispatchEx("Excel.Application")
excel.DisplayAlerts = False
excel.Visible = False

workbook = excel.Workbooks.Open('P:/02 - Agrícola/01 - Diário/2026/01 - Placar da Moagem/04 - Moagem V2 - Abr.26.xlsm')

workbook.RefreshAll()

while True:
    conexoes = listar_conexoes_em_refresh(workbook)

    if not conexoes:

        # FORÇA recálculo total (Power Pivot + fórmulas)
        excel.CalculateFullRebuild()

        excel.Run('SalvarTodos')

        workbook.Save()
        break

excel.DisplayAlerts = False
excel.Quit()
