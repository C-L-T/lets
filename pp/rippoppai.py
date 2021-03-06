"""
oppai interface for ripple 2 / LETS
"""
import json
import os
import subprocess

from common.constants import gameModes
from common.log import logUtils as log
from common.ripple import scoreUtils
from constants import exceptions
from helpers import mapsHelper

# constants
MODULE_NAME = "rippoppai"
UNIX = True if os.name == "posix" else False

def fixPath(command):
	"""
	Replace / with \ if running under WIN32

	commnd -- command to fix
	return -- command with fixed paths
	"""
	if UNIX:
		return command
	return command.replace("/", "\\")


class OppaiError(Exception):
	def __init__(self, error):
		self.error = error

class oppai:
	"""
	Oppai cacalculator
	"""

	# Folder where oppai is placed
	OPPAI_FOLDER = ".data/oppai"
	BUFSIZE = 2000000
	# __slots__ = ["pp", "score", "acc", "mods", "combo", "misses", "stars", "beatmap", "map"]

	def __init__(self, __beatmap, __score = None, acc = 0, mods = 0, tillerino = False):
		"""
		Set oppai params.

		__beatmap -- beatmap object
		__score -- score object
		acc -- manual acc. Used in tillerino-like bot. You don't need this if you pass __score object
		mods -- manual mods. Used in tillerino-like bot. You don't need this if you pass __score object
		tillerino -- If True, self.pp will be a list with pp values for 100%, 99%, 98% and 95% acc. Optional.
		"""
		# Default values
		self.pp = None
		self.score = None
		self.acc = 0
		self.mods = 0
		self.combo = 0
		self.misses = 0
		self.stars = 0
		self.tillerino = tillerino

		# Beatmap object
		self.beatmap = __beatmap
		self.map = "{}.osu".format(self.beatmap.beatmapID)

		# If passed, set everything from score object
		if __score is not None:
			self.score = __score
			self.acc = self.score.accuracy * 100
			self.mods = self.score.mods
			self.combo = self.score.maxCombo
			self.misses = self.score.cMiss
			self.gameMode = self.score.gameMode
		else:
			# Otherwise, set acc and mods from params (tillerino)
			self.acc = acc
			self.mods = mods

		# Calculate pp
		log.debug("oppai ~> Initialized oppai diffcalc")
		self.calculatePP()

	@staticmethod
	def _runOppaiProcess(command):
		log.debug("oppai ~> running {}".format(command))
		process = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
		try:
			output = json.loads(process.stdout.decode("utf-8", errors="ignore"))
			pp = output["pp"]
			stars = output["stars"]

			log.debug("oppai ~> full output: {}".format(output))
			log.debug("oppai ~> pp: {}, stars: {}".format(pp, stars))
		except (json.JSONDecodeError, IndexError):
			raise OppaiError("invalid json output")
		return pp, stars

	def calculatePP(self):
		"""
		Calculate total pp value with oppai and return it

		return -- total pp
		"""
		# Set variables
		self.pp = None
		try:
			# Build .osu map file path
			mapFile = "{path}/maps/{map}".format(path=self.OPPAI_FOLDER, map=self.map)
			log.debug("oppai ~> Map file: {}".format(mapFile))
			mapsHelper.cacheMap(mapFile, self.beatmap)

			# Use only mods supported by oppai
			modsFixed = self.mods & 5979
			command = "./pp/oppai-ng/oppai {}".format(mapFile)
			if not self.tillerino:
				# force acc only for non-tillerino calculation
				# acc is set for each subprocess if calculating tillerino-like pp sets
				if self.acc > 0:
					command += " {acc:.2f}%".format(acc=self.acc)
			if self.mods > 0:
				command += " +{mods}".format(mods=scoreUtils.readableMods(modsFixed))
			if self.combo > 0:
				command += " {combo}x".format(combo=self.combo)
			if self.misses > 0:
				command += " {misses}xm".format(misses=self.misses)
			if self.gameMode == gameModes.TAIKO:
				command += " -taiko"
			command += " -ojson"

			# Calculate pp
			if not self.tillerino:
				self.pp, self.stars = self._runOppaiProcess(command)
			else:
				pp_list = []
				for acc in [100, 99, 98, 95]:
					temp_command = command
					temp_command += " {acc:.2f}%".format(acc=acc)
					pp, self.stars = self._runOppaiProcess(temp_command)
					pp_list.append(pp)
				self.pp = pp_list

			log.debug("oppai ~> Calculated PP: {}, stars: {}".format(self.pp, self.stars))
		except OppaiError:
			log.error("oppai ~> oppai-ng error!")
			self.pp = 0
		except exceptions.osuApiFailException:
			log.error("oppai ~> osu!api error!")
			self.pp = 0
		except Exception as e:
			log.error("oppai ~> Unhandled exception: {}".format(str(e)))
			raise e
		finally:
			log.debug("oppai ~> Shutting down and returning {}pp".format(self.pp))
			return self.pp
