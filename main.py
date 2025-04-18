import pygame
import math

class GameObject:
	PADDLE = 10
	BALL = 20
	BRICK = 30

	def __init__(self, id: int, gameInstance: "Game"):
		self.gameInstance = gameInstance
		self.id = id
		self.deallocate = False
	
	def Update(self):
		pass

	def Render(self):
		pass

	def GetID(self):
		return self.id

	def CheckDeallocate(self):
		pass

"""
PhysicsGameObjects have different ways to store dimensions depending if
they're a circle or a rect. Currently they're stored in the immediate
inheriters of the class, but would a PhysicsRect and PhysicsCircle
that inherit from PhysicsGameObject be an improvement or overengineered?
"""
class PhysicsGameObject(GameObject):
	def __init__(self, id: int, gameInstance: "Game"):
		GameObject.__init__(self, id, gameInstance)
		self.pos = [0.0, 0.0]
		self.velocity = [0.0, 0.0]
		self.acceleration = [0.0, 0.0]
	
	def PushVelocity(self):
		self.pos = [self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1]]
	
	def AccelerateToLimit(self, limit: float):
		self.velocity = [self.velocity[0] + self.acceleration[0], self.velocity[1] + self.acceleration[1]]
		self.velocity = [Utility.minValue(limit, self.velocity[0]), Utility.minValue(limit, self.velocity[1])]
		self.velocity = [Utility.maxValue(-limit, self.velocity[0]), Utility.maxValue(-limit, self.velocity[1])]
	
	def AggressiveAccelerateToLimit(self, limit: float, change: float):
		# change applies different acceleration if the body is changing from one direction to another until it passes 0
		#ideally I would like this to be written without nested checks to work more like a math function

		for i in range(2):
			if self.acceleration[i] > 0:
				if self.velocity[i] < 0:
					self.velocity[i] = Utility.minValue(limit, self.velocity[i] + self.acceleration[i] * change)
				else:
					self.velocity[i] = Utility.minValue(limit, self.velocity[i] + self.acceleration[i])
			elif self.acceleration[i] < 0:
				if self.velocity[i] > 0:
					self.velocity[i] = Utility.maxValue(-limit, self.velocity[i] + self.acceleration[i] * change)
				else:
					self.velocity[i] = Utility.maxValue(-limit, self.velocity[i] + self.acceleration[i])
	
	def DragToZero(self, intensity: float):
		#cutoff means set to 0
		if self.velocity[0] > 0.0:
			self.velocity[0] = Utility.maxValue(0.0, self.velocity[0] - intensity)
		elif self.velocity[0] < 0.0:
			self.velocity[0] = Utility.minValue(0.0, self.velocity[0] + intensity)

		if self.velocity[1] > 0.0:
			self.velocity[1] = Utility.maxValue(0.0, self.velocity[1] - intensity)
		elif self.velocity[1] < 0.0:
			self.velocity[1] = Utility.minValue(0.0, self.velocity[1] + intensity)
	
	def GetCollisionShape(self):
		pass


#pygame don't have a circle so I'll handle it
class CircleCollider:
	def __init__(self, pos: list[float, float], radius: float):
		# no reference to pos
		self.pos = [pos[0], pos[1]]
		self.radius = radius
	
	def CircleCollide(self, circle: "CircleCollider"):
		d = Utility.distance(self.pos, circle.pos)
		return d < self.radius+circle.radius
	
	def RectCollide(self, rect: "pygame.Rect"):
		pos = [self.pos[0], self.pos[1]]
		pos[0] = Utility.maxValue(pos[0], rect.left)
		pos[0] = Utility.minValue(pos[0], rect.right)
		pos[1] = Utility.maxValue(pos[1], rect.top)
		pos[1] = Utility.minValue(pos[1], rect.bottom)
		return Utility.distance(pos, self.pos) < self.radius
	
	def GetRectCollisionSide(self, rect: "pygame.Rect"):
		pos = [self.pos[0], self.pos[1]]
		pos[0] = Utility.maxValue(pos[0], rect.left)
		pos[0] = Utility.minValue(pos[0], rect.right)
		pos[1] = Utility.maxValue(pos[1], rect.top)
		pos[1] = Utility.minValue(pos[1], rect.bottom)

		return [
			-1 if pos[0] == rect.left else (1 if pos[0] == rect.right else 0),
			-1 if pos[1] == rect.top else (1 if pos[1] == rect.bottom else 0)
		]
	
	def GetRectCollisionSide2(self, rect: "pygame.Rect"):
		difference = [self.pos[0]-rect.centerx, self.pos[1]-rect.centery]
		
		if rect.width > rect.height:
			difference[0] *= float(rect.height)/float(rect.width)
		else:
			difference[1] *= float(rect.width)/float(rect.height)

		if abs(difference[0]) > abs(difference[1]):
			return [-1, 0] if difference[0] < 0 else [1, 0]
		else:
			return [0, -1] if difference[1] < 0 else [0, 1]


class Paddle(PhysicsGameObject):
	def __init__(self, gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.PADDLE, gameInstance)


		self.pos = [gameInstance.dim[0]/2+20, gameInstance.dim[1]*15/16]
		self.dim = [100, 10]
		self.maxMoveSpeed = 10
		self.accelerationSpeed = 1
		self.accelerationBrakeSpeed = 2

		self.reflectionIntensity = 5

	def GetCollisionShape(self):
		return pygame.Rect(
			self.pos[0] - self.dim[0]/2,
			self.pos[1] - self.dim[1]/2,
			self.dim[0],
			self.dim[1]
		)

	def Update(self):
		self.PushVelocity()
		self.AggressiveAccelerateToLimit(self.maxMoveSpeed, self.accelerationBrakeSpeed)
		
		if self.gameInstance.controller.LEFT:
			self.acceleration[0] = -self.accelerationSpeed
		elif self.gameInstance.controller.RIGHT:
			self.acceleration[0] = self.accelerationSpeed
		else:
			self.acceleration[0] = 0.0
			self.DragToZero(2.0)

		self.pos[0] = Utility.maxValue(self.dim[0]/2, self.pos[0])
		self.pos[0] = Utility.minValue(self.gameInstance.dim[0]-self.dim[0]/2, self.pos[0])

	def Render(self):
		pygame.draw.rect(self.gameInstance.window, (255, 255, 255), [self.pos[0] - self.dim[0]/2, self.pos[1] - self.dim[1]/2, self.dim[0], self.dim[1]])


class Brick(PhysicsGameObject):
	defaultDim = (60, 20)
	colors = (
		(50,10,225),
		(30,170,60),
		(225,240,65),
		(210,55,55)
	)

	def __init__(self, pos: list[float, float], gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.BRICK, gameInstance)
		self.pos = [pos[0], pos[1]]
		self.dim = [Brick.defaultDim[0], Brick.defaultDim[1]]
		self.health = 4
	
	def Damage(self):
		self.health -= 1
		if self.health == 0:
			self.deallocate = True

	def GetCollisionShape(self):
		return pygame.Rect(
			self.pos[0] - self.dim[0]/2,
			self.pos[1] - self.dim[1]/2,
			self.dim[0],
			self.dim[1]
		)

	def Update(self):
		pass

	def Render(self):
		pygame.draw.rect(self.gameInstance.window, Brick.colors[self.health-1], [self.pos[0] - self.dim[0]/2, self.pos[1] - self.dim[1]/2, self.dim[0], self.dim[1]])


class Ball(PhysicsGameObject):
	def __init__(self, gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.BALL, gameInstance)
		self.velocity = [0.0, 0.0]
		self.moveSpeed = 5
		self.radius = 6
		self.startDelay = self.gameInstance.gameTime + 60
	
	def SetDirection(self, relativePosition: list[float, float]):
		d = math.sqrt(relativePosition[0]*relativePosition[0]+relativePosition[1]*relativePosition[1])
		self.velocity = [relativePosition[0]/d*self.moveSpeed, relativePosition[1]/d*self.moveSpeed]
	

	def ResetStartTimer(self):
		self.startDelay = self.gameInstance.gameTime + 60

	def GetCollisionShape(self) -> CircleCollider:
		return CircleCollider(self.pos, self.radius)

	# grabbing objects from a general array means that pylance doesn't provide hints
	# I thought about switching collision checking to paddle and bricks, but doing it this way creates fewer checks
	def CheckCollisions(self):
		circle = self.GetCollisionShape()
		for obj in self.gameInstance.instance:
			if obj.id == GameObject.PADDLE:
				rect = obj.GetCollisionShape()
				if circle.RectCollide(rect) and self.velocity[1] > 0:
					direction = [self.pos[0] - obj.pos[0], self.pos[1] - (obj.pos[1]+100/obj.reflectionIntensity)]
					self.SetDirection(direction)
			elif obj.id == GameObject.BRICK:
				rect = obj.GetCollisionShape()
				if circle.RectCollide(rect) and obj.deallocate == False:
					obj.Damage()
					sides = circle.GetRectCollisionSide2(rect)
					self.velocity[0] = -self.velocity[0] if sides[0] != 0 else self.velocity[0]
					self.velocity[1] = -self.velocity[1] if sides[1] != 0 else self.velocity[1]
					self.pos[0] = rect.left - self.radius if sides[0] < 0 else (rect.right + self.radius if sides[0] > 0 else self.pos[0])
					self.pos[1] = rect.top - self.radius if sides[1] < 0 else (rect.bottom + self.radius if sides[1] > 0 else self.pos[1])

	def Update(self):
		if self.startDelay > self.gameInstance.gameTime:
			return
		self.pos = [self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1]]

		if self.velocity[0] > 0 and self.pos[0]+self.radius > self.gameInstance.dim[0]:
			self.velocity[0] = -self.velocity[0]
		elif self.velocity[0] < 0 and self.pos[0] - self.radius < 0:
			self.velocity[0] = -self.velocity[0]

		if self.velocity[1] < 0 and self.pos[1] - self.radius < 0:
			self.velocity[1] = -self.velocity[1]

		self.CheckCollisions()

	def Render(self):
		pygame.draw.circle(self.gameInstance.window, (255, 255, 255), self.pos, self.radius)


class Controller:
	def __init__(self):
		self.LEFT = False
		self.RIGHT = False
		self.ACTION = False


class Utility:
	def angleToRandian(n: float):
		return n*math.pi/180

	def minValue(a, b):
		return a if a < b else b

	def maxValue(a, b):
		return a if a > b else b

	def distance(pos1: list[float, float], pos2: list[float, float]):
		return math.sqrt((pos1[0]-pos2[0])*(pos1[0]-pos2[0])+(pos1[1]-pos2[1])*(pos1[1]-pos2[1]))

	def NormalizeVector(vec: list[float, float], magnitude: int = 1):
		d = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
		return [vec[0]/d*magnitude, vec[1]/d*magnitude]

	def VectorMultiply(vec1: list[float, float], vec2: list[float, float]):
		vec3 = [vec1[0]*vec2[0]-vec1[1]+vec2[1], vec1[0]*vec2[1]+vec1[1]*vec2[0]]
		return Utility.NormalizeVector(vec3)


class LevelGenerator:
	def ResetLevel(gameInstance: "Game"):
		gameInstance.instance = []
		gameInstance.ballLives = 3

		paddle = Paddle(gameInstance)

		ball = Ball(gameInstance)
		ball.pos = [gameInstance.dim[0]/2, 500]
		ball.SetDirection([0.0, 1.0])

		gameInstance.instance.append(ball)
		gameInstance.instance.append(paddle)

		topMargin = 30
		bottomMargin = 350
		leftMargin = 40
		rightMargin = 40

		verticalSpacing = 10
		horizontalSpacing = 10
		# this implementation for a level generator is janky and causes weird spacing
		for y in range(int(Brick.defaultDim[1]/2 + topMargin), int(gameInstance.dim[1] - Brick.defaultDim[1]/2 - bottomMargin), int(verticalSpacing + Brick.defaultDim[1])):
			for x in range(int(Brick.defaultDim[0]/2 + leftMargin), int(gameInstance.dim[0] - Brick.defaultDim[0]/2 - rightMargin), int(horizontalSpacing + Brick.defaultDim[0])):
				gameInstance.instance.append(Brick([x, y], gameInstance))


class GameUI:
	def RenderLives(gameInstance: "Game"):
		leftMargin = 10
		topMargin = 10
		lifeOffset = 16

		outerLayer = 8
		innerLayer = 4

		for x in range(0, gameInstance.ballLives, 1):
			pygame.draw.circle(gameInstance.window, (0, 0, 0), (leftMargin + lifeOffset*x, topMargin), outerLayer)
			pygame.draw.circle(gameInstance.window, (255, 255, 255), (leftMargin + lifeOffset*x, topMargin), innerLayer)


class Game:
	def __init__(self):
		self.window = None
		self.running = True
		self.dim = (800, 800)

		self.ballLives = 3

		self.controller = Controller()

		self.instance = []

		self.gameTime = 0

		self.backgroundColor = (100, 100, 100)

	def Start(self):

		LevelGenerator.ResetLevel(self)
	
	def Input(self):
		for e in pygame.event.get():
			if e.type == pygame.QUIT:
				self.running = False
			elif e.type == pygame.KEYDOWN:
				if e.key == pygame.K_a or e.key == pygame.K_LEFT:
					self.controller.LEFT = True
				elif e.key == pygame.K_d or e.key == pygame.K_RIGHT:
					self.controller.RIGHT = True
			elif e.type == pygame.KEYUP:
				if e.key == pygame.K_a or e.key == pygame.K_LEFT:
					self.controller.LEFT = False
				elif e.key == pygame.K_d or e.key == pygame.K_RIGHT:
					self.controller.RIGHT = False

	def Update(self):
		for obj in self.instance:
			obj.Update()
		
		for i in range(len(self.instance)-1, -1, -1):
			obj = self.instance[i]
			if obj.deallocate:
				self.instance.remove(obj)
		
		# life counter only supports 1 ball in game instance
		# once again pylance doesn't recognize the ball as a Ball instance

		arr = [i for i in self.instance if isinstance(i, Ball)]

		if len(arr) > 0:
			ball = arr[0]
			if ball.pos[1] > self.dim[1]:
				self.ballLives -= 1
				ball.pos = [self.dim[0]/2, 500]
				ball.SetDirection([0.0, 1.0])
				ball.ResetStartTimer()
				if self.ballLives < 0:
					LevelGenerator.ResetLevel(self)

	def Render(self):
		self.window.fill(self.backgroundColor)

		for obj in self.instance:
			obj.Render()
		
		GameUI.RenderLives(self)

		pygame.display.flip()

	def main(self):
		pygame.init()

		self.window = pygame.display.set_mode(self.dim)

		tps = 60.0
		ns = 1000.0 / tps
		actualTPS = 0

		delta = 0.0

		lastTime = pygame.time.get_ticks()

		fps = 144.0
		frameNS = 1000.0 / fps
		actualFPS = 0

		lastFrame = pygame.time.get_ticks()

		timer = pygame.time.get_ticks()

		reportRefreshRate = False

		self.Start()

		while self.running:
			self.Input()

			nowTime = pygame.time.get_ticks()
			delta += float(nowTime-lastTime) / ns
			lastTime = nowTime

			while not (delta < 1):
				self.Update()
				self.gameTime += 1
				actualTPS += 1
				delta -= 1.0
			
			nowFrame = pygame.time.get_ticks()
			if float(nowFrame-lastFrame) > frameNS:
				lastFrame = nowFrame
				self.Render()
				actualFPS += 1
			
			nowTimer = pygame.time.get_ticks()
			if nowTimer - timer > 1000:
				timer = nowTimer
				if reportRefreshRate:
					print(f"TPS: {actualTPS}\nFPS: {actualFPS}")
				actualTPS = 0
				actualFPS = 0

		pygame.quit()


if __name__ == "__main__":
	g = Game()
	g.main()
