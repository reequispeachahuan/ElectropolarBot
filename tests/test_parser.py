from app.seace.parser import parse_result_table


def test_parse_result_table_skips_empty_seace_rows():
    html = """
    <table>
      <tr><th>Nomenclatura</th><th>Descripcion</th></tr>
      <tr><td>No se encontraron Datos</td></tr>
      <tr><td>Sin información</td></tr>
    </table>
    """

    assert parse_result_table(html, "seace") == []


def test_parse_result_table_normalizes_simple_rows():
    html = """
    <table>
      <tr><th>Nomenclatura</th><th>Descripcion</th></tr>
      <tr><td>LP-001</td><td>Compra de panel solar <a href="https://example.com/ficha">Ficha</a></td></tr>
    </table>
    """

    assert parse_result_table(html, "seace") == [
        {
            "nomenclatura": "LP-001",
            "descripcion": "Compra de panel solar Ficha",
            "url": "https://example.com/ficha",
            "source": "seace",
        }
    ]


def test_parse_result_table_ignores_container_table_with_nested_result_table():
    html = """
    <table>
      <tr><td>
        <table>
          <thead>
            <tr><th>N°</th><th>Nomenclatura</th><th>Descripción de Objeto</th></tr>
          </thead>
          <tbody>
            <tr><td>1</td><td>LP-001</td><td>Compra de panel solar</td></tr>
          </tbody>
        </table>
      </td></tr>
    </table>
    """

    assert parse_result_table(html, "seace") == [
        {
            "n°": "1",
            "nomenclatura": "LP-001",
            "descripcion de objeto": "Compra de panel solar",
            "source": "seace",
        }
    ]
