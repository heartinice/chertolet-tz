"""Модульные проверки; номера совпадают с TEST_CASES.md."""

import pytest

from chertolet import Chertolet, ChertoletError, FlightStateError


def test_TC_M_001_defaults():
    c = Chertolet()
    assert c.get_status() == dict(name="Грешник-3000", sin_level=0,
        boost_kmh=0.0, speed_kmh=0.0, position_km=0.0, is_flying=False)
    expected = dict(name=str, sin_level=int, boost_kmh=float,
        speed_kmh=float, position_km=float, is_flying=bool)
    assert {key: type(value) for key, value in c.get_status().items()} == expected


def test_TC_M_002_custom_init():
    c = Chertolet("  Люцифер-экспресс  ", 50)
    assert c.name == "Люцифер-экспресс"
    assert c.sin_level == 50
    assert c.boost_kmh == 100.0
    assert c.speed_kmh == 0.0


@pytest.mark.parametrize("name,error,message", [
    ("", ValueError, "name must not be blank"),
    (" \t\n", ValueError, "name must not be blank"),
    (None, TypeError, "name must be a string"),
    (12, TypeError, "name must be a string"),
    (True, TypeError, "name must be a string"),
])
def test_TC_M_003_bad_name(name, error, message):
    with pytest.raises(error) as exc:
        Chertolet(name)
    assert str(exc.value) == message


@pytest.mark.parametrize("level", [0, 1, 50, 99, 100])
def test_TC_M_004_sin_bounds(level):
    c = Chertolet(sin_level=level)
    assert c.sin_level == level
    assert type(c.sin_level) is int


@pytest.mark.parametrize("level", [-1, 101, 10**1000])
def test_TC_M_005_bad_sin_range(level):
    with pytest.raises(ValueError, match="^sin_level must be between 0 and 100$"):
        Chertolet(sin_level=level)


@pytest.mark.parametrize("level", [0.0, 50.5, "50", None, True, False, float("nan"), float("inf")])
def test_TC_M_006_bad_sin_type(level):
    with pytest.raises(TypeError, match="^sin_level must be an integer$"):
        Chertolet(sin_level=level)


@pytest.mark.parametrize("attr,value", [("name", "X"), ("sin_level", 1),
    ("boost_kmh", 2.0), ("speed_kmh", 32.0), ("position_km", 1.0), ("is_flying", True)])
def test_TC_M_007_read_only(attr, value):
    c = Chertolet()
    before = c.get_status()
    with pytest.raises(AttributeError):
        setattr(c, attr, value)
    assert c.get_status() == before


@pytest.mark.parametrize("level,speed", [(0, 30.0), (1, 32.0), (50, 130.0), (100, 230.0)])
def test_TC_M_008_take_off_speed(level, speed):
    c = Chertolet(sin_level=level)
    assert c.take_off() is None
    assert c.is_flying is True
    assert c.speed_kmh == speed
    assert type(c.speed_kmh) is float
    assert c.position_km == 0.0
    assert c.sin_level == level


def test_TC_M_009_double_take_off():
    c = Chertolet(sin_level=10)
    c.take_off()
    before = c.get_status()
    with pytest.raises(FlightStateError, match="^already flying$"):
        c.take_off()
    assert c.get_status() == before


def test_TC_M_010_land():
    c = Chertolet(sin_level=50)
    c.take_off()
    c.move(13)
    assert c.land() is None
    assert c.get_status() == dict(name="Грешник-3000", sin_level=50,
        boost_kmh=100.0, speed_kmh=0.0, position_km=13.0, is_flying=False)


def test_TC_M_011_land_on_ground():
    c = Chertolet()
    before = c.get_status()
    with pytest.raises(FlightStateError, match="^already on ground$"):
        c.land()
    assert c.get_status() == before


@pytest.mark.parametrize("distance,level,time", [(30, 0, 1.0), (13.0, 50, 0.1),
    (0.5, 100, 0.5 / 230), (1_000_000, 0, 1_000_000 / 30)])
def test_TC_M_012_move(distance, level, time):
    c = Chertolet(sin_level=level)
    c.take_off()
    duration = c.move(distance)
    assert type(duration) is float
    assert duration == pytest.approx(time)
    assert c.position_km == pytest.approx(distance)
    assert type(c.position_km) is float
    assert c.sin_level == level
    assert c.is_flying is True


def test_TC_M_013_ground_move():
    c = Chertolet(sin_level=100)
    before = c.get_status()
    with pytest.raises(FlightStateError, match="^cannot move on ground$"):
        c.move(1)
    assert c.get_status() == before


@pytest.mark.parametrize("flying", [False, True])
@pytest.mark.parametrize("distance", [0, -1, 1_000_001, 10**1000,
    float("inf"), float("-inf"), float("nan")])
def test_TC_M_014_bad_distance_range(flying, distance):
    c = Chertolet()
    if flying:
        c.take_off()
        c.move(1)
    before = c.get_status()
    with pytest.raises(ValueError) as exc:
        c.move(distance)
    assert str(exc.value) == "distance_km must be between 0 (exclusive) and 1000000"
    assert c.get_status() == before


@pytest.mark.parametrize("flying", [False, True])
@pytest.mark.parametrize("distance", ["1", None, True, False, [], complex(1, 0)])
def test_TC_M_015_bad_distance_type(flying, distance):
    c = Chertolet()
    if flying:
        c.take_off()
        c.move(1)
    before = c.get_status()
    with pytest.raises(TypeError, match="^distance_km must be a number$"):
        c.move(distance)
    assert c.get_status() == before


@pytest.mark.parametrize("flying", [False, True])
def test_TC_M_016_add_sins(flying):
    c = Chertolet(sin_level=10)
    if flying:
        c.take_off()
        c.move(5)
    assert c.add_sins(1) is None
    assert c.sin_level == 11
    assert c.boost_kmh == 22.0
    assert c.speed_kmh == (52.0 if flying else 0.0)
    assert c.position_km == (5.0 if flying else 0.0)
    assert c.is_flying is flying


@pytest.mark.parametrize("level,amount", [(0, 100), (99, 1), (90, 20), (100, 100)])
def test_TC_M_017_sin_cap(level, amount):
    c = Chertolet(sin_level=level)
    c.take_off()
    c.add_sins(amount)
    assert c.sin_level == 100
    assert c.speed_kmh == 230.0


@pytest.mark.parametrize("flying", [False, True])
@pytest.mark.parametrize("amount", [0, -1, 101, 10**1000])
def test_TC_M_018_bad_amount_range(flying, amount):
    c = Chertolet(sin_level=10)
    if flying:
        c.take_off()
    before = c.get_status()
    with pytest.raises(ValueError, match="^amount must be between 1 and 100$"):
        c.add_sins(amount)
    assert c.get_status() == before


@pytest.mark.parametrize("flying", [False, True])
@pytest.mark.parametrize("amount", [1.0, "1", None, True, False, float("nan"), float("inf")])
def test_TC_M_019_bad_amount_type(flying, amount):
    c = Chertolet(sin_level=10)
    if flying:
        c.take_off()
    before = c.get_status()
    with pytest.raises(TypeError, match="^amount must be an integer$"):
        c.add_sins(amount)
    assert c.get_status() == before


@pytest.mark.parametrize("flying", [False, True])
@pytest.mark.parametrize("level", [0, 1, 100])
def test_TC_M_020_absolution(flying, level):
    c = Chertolet(sin_level=level)
    if flying:
        c.take_off()
        c.move(5)
    assert c.absolve_sins() is None
    assert c.sin_level == 0
    assert c.boost_kmh == 0.0
    assert c.speed_kmh == (30.0 if flying else 0.0)
    assert c.position_km == (5.0 if flying else 0.0)
    assert c.is_flying is flying
    assert c.name == "Грешник-3000"
    before = c.get_status()
    c.absolve_sins()
    assert c.get_status() == before
    c.add_sins(1)
    assert c.sin_level == 1 and c.boost_kmh == 2.0
    assert c.speed_kmh == (32.0 if flying else 0.0)
    assert c.position_km == before["position_km"]
    assert c.is_flying is flying


def test_TC_M_021_snapshot():
    c = Chertolet(sin_level=50)
    old = c.get_status()
    c.take_off()
    c.move(13)
    current = c.get_status()
    assert old["position_km"] == 0.0 and old["is_flying"] is False
    assert current == dict(name="Грешник-3000", sin_level=50,
        boost_kmh=100.0, speed_kmh=130.0, position_km=13.0, is_flying=True)
    current.clear()
    assert c.get_status()["position_km"] == 13.0
    assert c.get_status()["sin_level"] == 50


def test_TC_M_022_exception_hierarchy():
    assert issubclass(ChertoletError, RuntimeError)
    assert issubclass(FlightStateError, ChertoletError)
    with pytest.raises(ChertoletError):
        Chertolet().move(1)


def test_TC_M_023_independent_instances():
    a, b = Chertolet(), Chertolet()
    before = b.get_status()
    a.add_sins(50)
    a.take_off()
    a.move(13)
    assert b.get_status() == before


def test_TC_M_024_constructor_validation_order():
    with pytest.raises(TypeError, match="^name must be a string$"):
        Chertolet(None, -1)
    with pytest.raises(ValueError, match="^name must not be blank$"):
        Chertolet(" ", True)
