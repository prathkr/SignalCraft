import random
import time
import threading
import pygame
import sys

defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
minGreen = 5
maxGreen = 30
defaultRed = 150
defaultYellow = 5
dark_bg = (50, 50, 50)

signals = []
noOfSignals = 4
currentGreen = 0
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0

speeds = {"car": 0.35, "bus": 0.15, "truck": 0.2, "bike": 0.6}


x = {
    "right": [0, 0, 0],
    "down": [755, 727, 697],
    "left": [1400, 1400, 1400],
    "up": [602, 627, 657],
}
y = {
    "right": [348, 370, 398],
    "down": [0, 0, 0],
    "left": [478, 446, 426],
    "up": [800, 800, 800],
}

vehicles = {
    "right": {0: [], 1: [], 2: [], "crossed": 0},
    "down": {0: [], 1: [], 2: [], "crossed": 0},
    "left": {0: [], 1: [], 2: [], "crossed": 0},
    "up": {0: [], 1: [], 2: [], "crossed": 0},
}
vehicleTypes = {0: "car", 1: "bus", 2: "truck", 3: "bike"}
directionNumbers = {0: "right", 1: "down", 2: "left", 3: "up"}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
vehicleCountCoods = [(350, 300), (1000, 300), (1000, 550), (350, 550)]


stopLines = {"right": 590, "down": 330, "left": 800, "up": 535}
defaultStop = {"right": 580, "down": 320, "left": 810, "up": 545}


stoppingGap = 15
movingGap = 15


signal_initialized = threading.Event()

pygame.init()
simulation = pygame.sprite.Group()


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        self.vehicleCount = 0


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        if (
            len(vehicles[direction][lane]) > 1
            and vehicles[direction][lane][self.index - 1].crossed == 0
        ):  
            if direction == "right":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    - vehicles[direction][lane][self.index - 1].image.get_rect().width
                    - stoppingGap
                )  
            elif direction == "left":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    + vehicles[direction][lane][self.index - 1].image.get_rect().width
                    + stoppingGap
                )
            elif direction == "down":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    - vehicles[direction][lane][self.index - 1].image.get_rect().height
                    - stoppingGap
                )
            elif direction == "up":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    + vehicles[direction][lane][self.index - 1].image.get_rect().height
                    + stoppingGap
                )
        else:
            self.stop = defaultStop[direction]

        if direction == "right":
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] -= temp
        elif direction == "left":
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif direction == "down":
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif direction == "up":
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if self.direction == "right":
            if (
                self.crossed == 0
                and self.x + self.image.get_rect().width > stopLines[self.direction]
            ):
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
            if (
                self.x + self.image.get_rect().width <= self.stop
                or self.crossed == 1
                or (currentGreen == 0 and currentYellow == 0)
            ) and (
                self.index == 0
                or self.x + self.image.get_rect().width
                < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap)
            ):

                self.x += self.speed
        elif self.direction == "down":
            if (
                self.crossed == 0
                and self.y + self.image.get_rect().height > stopLines[self.direction]
            ):
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
            if (
                self.y + self.image.get_rect().height <= self.stop
                or self.crossed == 1
                or (currentGreen == 1 and currentYellow == 0)
            ) and (
                self.index == 0
                or self.y + self.image.get_rect().height
                < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap)
            ):
                self.y += self.speed
        elif self.direction == "left":
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
            if (
                self.x >= self.stop
                or self.crossed == 1
                or (currentGreen == 2 and currentYellow == 0)
            ) and (
                self.index == 0
                or self.x
                > (
                    vehicles[self.direction][self.lane][self.index - 1].x
                    + vehicles[self.direction][self.lane][self.index - 1]
                    .image.get_rect()
                    .width
                    + movingGap
                )
            ):
                self.x -= self.speed
        elif self.direction == "up":
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
            if (
                self.y >= self.stop
                or self.crossed == 1
                or (currentGreen == 3 and currentYellow == 0)
            ) and (
                self.index == 0
                or self.y
                > (
                    vehicles[self.direction][self.lane][self.index - 1].y
                    + vehicles[self.direction][self.lane][self.index - 1]
                    .image.get_rect()
                    .height
                    + movingGap
                )
            ):
                self.y -= self.speed


def count_vehicles_in_direction(direction):
    counts = {"bike": 0, "car": 0, "truck": 0, "bus": 0}
    for lane in range(3):
        for vehicle in vehicles[direction][lane]:
            if vehicle.crossed == 0:
                counts[vehicle.vehicleClass] += 1
    global vehicle_count
    vehicle_count = sum(counts.values())
    return counts


def calculate_green_time(vehicle_counts):

    weights = {"car": 0.1, "bus": 0.3, "truck": 0.2, "bike": 0.05}

    weighted_density = sum(
        count * weights[vehicle_type] * (1 / speeds[vehicle_type])
        for vehicle_type, count in vehicle_counts.items()
    )
    max_density = 25.0

    if weighted_density == 0:
        return minGreen

    if weighted_density >= max_density:
        return maxGreen
    else:

        green_time = minGreen + (maxGreen - minGreen) * (weighted_density / max_density)
        return round(green_time)


def initialize():
    global signals
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
    signals.append(ts1)
    ts2 = TrafficSignal(
        ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen[1]
    )
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
    signals.append(ts4)

    signal_initialized.set()

    repeat()


def repeat():
    global currentGreen, currentYellow, nextGreen

    for i in range(noOfSignals):
        direction = directionNumbers[i]
        signals[i].vehicleCount = count_vehicles_in_direction(direction)

    dynamic_green_time = calculate_green_time(signals[currentGreen].vehicleCount)
    signals[currentGreen].green = dynamic_green_time

    while signals[currentGreen].green > 0:
        updateValues()
        time.sleep(1)

        for i in range(noOfSignals):
            direction = directionNumbers[i]
            signals[i].vehicleCount = count_vehicles_in_direction(direction)

    currentYellow = 1

    for i in range(0, 3):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while signals[currentGreen].yellow > 0:
        updateValues()
        time.sleep(1)
    currentYellow = 0

    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed

    currentGreen = nextGreen
    nextGreen = (currentGreen + 1) % noOfSignals

    next_green_time = calculate_green_time(signals[currentGreen].vehicleCount)
    signals[currentGreen].green = next_green_time

    signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green
    repeat()


def updateValues():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


def generateVehicles():

    signal_initialized.wait()

    while True:
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(0, 2)
        temp = random.randint(0, 99)
        direction_number = 0
        dist = [25, 50, 75, 100]
        if temp < dist[0]:
            direction_number = 0
        elif temp < dist[1]:
            direction_number = 1
        elif temp < dist[2]:
            direction_number = 2
        elif temp < dist[3]:
            direction_number = 3
        Vehicle(
            lane_number,
            vehicleTypes[vehicle_type],
            direction_number,
            directionNumbers[direction_number],
        )
        time.sleep(1)


thread1 = threading.Thread(name="initialization", target=initialize, args=())
thread1.daemon = True
thread1.start()


black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)


screenWidth = 1400
screenHeight = 800
screenSize = (screenWidth, screenHeight)


background = pygame.image.load("images/intersection.png")

screen = pygame.display.set_mode(screenSize)
pygame.display.set_caption("TRAFFIC SIMULATION WITH DYNAMIC TIMING")


redSignal = pygame.image.load("images/signals/red.png")
yellowSignal = pygame.image.load("images/signals/yellow.png")
greenSignal = pygame.image.load("images/signals/green.png")
font = pygame.font.Font(None, 30)


thread2 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())
thread2.daemon = True
thread2.start()


signal_initialized.wait()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    screen.blit(background, (0, 0))

    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 1:
                signals[i].signalText = signals[i].yellow
                screen.blit(yellowSignal, signalCoods[i])
            else:
                signals[i].signalText = signals[i].green
                screen.blit(greenSignal, signalCoods[i])
        else:
            if signals[i].red <= 10:
                signals[i].signalText = signals[i].red
            else:
                signals[i].signalText = "---"
            screen.blit(redSignal, signalCoods[i])

    signalTexts = ["", "", "", ""]
    vehicleCountTexts = ["", "", "", ""]
    vehicleCountRects = []

    for i in range(0, noOfSignals):

        signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
        screen.blit(signalTexts[i], signalTimerCoods[i])

        counts = signals[i].vehicleCount
        count_text = f"Bike:{counts['bike']} Car:{counts['car']} Truck:{counts['truck']} Bus:{counts['bus']}"
        vehicleCountTexts[i] = font.render(count_text, True, white, dark_bg)

        text_rect = vehicleCountTexts[i].get_rect(center=vehicleCountCoods[i])
        bg_rect = pygame.Rect(
            text_rect.left - 5,
            text_rect.top - 2,
            text_rect.width + 10,
            text_rect.height + 4,
        )

        pygame.draw.rect(screen, dark_bg, bg_rect)
        screen.blit(vehicleCountTexts[i], text_rect)

    for vehicle in simulation:
        screen.blit(vehicle.image, [vehicle.x, vehicle.y])
        vehicle.move()

    pygame.display.update()

