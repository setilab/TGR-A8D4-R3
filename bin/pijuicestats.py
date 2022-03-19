from pijuice import PiJuice
pijuice = PiJuice(1, 0x14)
status = pijuice.status.GetStatus()
charge = pijuice.status.GetChargeLevel()

battery = { 'status':status["data"].get("battery"),
            'charge':charge["data"]
          }

print(battery)
