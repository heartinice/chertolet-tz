"""Сценарии Given / When / Then без подмены реальной реализации."""

import pytest

from chertolet import Chertolet, FlightStateError


def test_TC_S_001_sinner_route():
    # Given: 50 грехов, аппарат на земле.
    c = Chertolet(sin_level=50)
    # When: взлёт, два участка, посадка.
    c.take_off()
    times = [c.move(13), c.move(26)]
    c.land()
    # Then: 39 км за 0.3 часа; грехи сохранены.
    assert times == pytest.approx([0.1, 0.2])
    assert c.position_km == 39.0
    assert c.sin_level == 50
    assert c.speed_kmh == 0.0
    assert c.is_flying is False


def test_TC_S_002_absolution_in_air():
    # Given: грешник с максимальным ускорением в полёте.
    c = Chertolet(sin_level=100)
    c.take_off()
    # When: 23 км, отпущение грехов, ещё 3 км.
    first = c.move(23)
    c.absolve_sins()
    assert c.is_flying is True
    assert c.speed_kmh == 30.0 and c.boost_kmh == 0.0
    second = c.move(3)
    # Then: прошлое время не пересчитывается, новый участок медленнее.
    assert (first, second) == pytest.approx((0.1, 0.1))
    assert c.position_km == 26.0 and c.sin_level == 0


def test_TC_S_003_sin_again():
    # Given: полёт без грехов.
    c = Chertolet()
    c.take_off()
    # When: чистый участок, новые грехи, достижение лимита.
    times = [c.move(3)]
    c.add_sins(50)
    times.append(c.move(13))
    c.add_sins(80)
    times.append(c.move(23))
    # Then: скорость меняется для каждого следующего участка.
    assert times == pytest.approx([0.1, 0.1, 0.1])
    assert c.position_km == 39.0
    assert c.sin_level == 100 and c.speed_kmh == 230.0


def test_TC_S_004_error_and_resume():
    # Given: аппарат пролетел 5 км и сел.
    c = Chertolet(sin_level=10)
    c.take_off()
    assert c.move(5) == pytest.approx(0.1)
    c.land()
    before = c.get_status()
    # When: неверные команды, затем исправление и новый вылет.
    for action, error in [(lambda: c.move(1), FlightStateError),
                          (lambda: c.move(0), ValueError),
                          (lambda: c.add_sins(True), TypeError)]:
        with pytest.raises(error):
            action()
        assert c.get_status() == before
    c.absolve_sins()
    c.take_off()
    assert c.move(3) == pytest.approx(0.1)
    c.land()
    # Then: продолжение маршрута не потеряло уже пройденный путь.
    assert c.position_km == 8.0
    assert c.sin_level == 0 and c.is_flying is False


def test_TC_S_005_ground_absolution():
    # Given: грешник завершил первый рейс.
    c = Chertolet(sin_level=100)
    c.take_off()
    c.move(23)
    c.land()
    # When: отпущение на земле и повторный рейс.
    c.absolve_sins()
    assert c.speed_kmh == 0.0 and c.boost_kmh == 0.0
    c.take_off()
    assert c.speed_kmh == 30.0
    assert c.move(3) == pytest.approx(0.1)
    # Then: старое ускорение не восстановилось после взлёта.
    assert c.position_km == 26.0 and c.sin_level == 0
