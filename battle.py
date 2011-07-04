import utility

import pyglet
from pyglet.window import key, mouse

import cocos
from cocos import tiles, actions, layer, rect
from cocos.director import director

class Stats(object):
    def __init__(self):
        self._hp = 0
        self._max_hp = 0
        self._atk = 0
        self._def = 0
        self._speed = 0
def random_stats():
    import random
    s = Stats()
    s._hp = random.randint(30,100)
    s._max_hp = s._hp
    s._atk = random.randint(10,30)
    s._def = random.randint(10,30)
    s._speed = random.randint(10,30)
    return s

class Combatant(cocos.sprite.Sprite):
    def __init__(self, name, battle, image):
        super(Combatant, self).__init__(image)
        self.name = name
        self.battle = battle
        self.stats = random_stats()
        # Action points
        self.ap = 0

    def attack(self, opponent):
        damage = self.stats._atk * (1.0 - (opponent.stats._def / 100.0))
        opponent.stats._hp -= damage
        self.dispatch_event('on_damage', self, opponent, damage)
        if opponent.stats._hp <= 0:
            self.dispatch_event('on_death', opponent)

    def heal(self, health):
        self.stats._hp = min(self.stats._hp + health, self.stats._max_hp)
        self.dispatch_event('on_heal', self, health)
    
    def take_turn(self):
        pass
Combatant.register_event_type('on_death')
Combatant.register_event_type('on_damage')
Combatant.register_event_type('on_heal')

class Enemy(Combatant):
    def take_turn(self):
        ally = self.battle.allies[0]
        self.attack(ally)
        def next_turn():
            self.battle.next_turn()
        self.do(cocos.actions.Delay(.4) + cocos.actions.CallFunc(next_turn))

class AllyMenu(cocos.menu.Menu):
    def __init__(self, ally, on_attack, on_guard):
        self.ally = ally
        super(AllyMenu, self).__init__('%s\'s Turn' % self.ally.name)
        # Menu item font properties
        self.font_title['font_name'] = 'Sans'
        self.font_title['color'] = (255, 255, 255, 255)
        self.font_item['font_name'] = 'Sans'
        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item_selected['font_name'] = 'Sans'
        self.font_item_selected['color'] = (128, 128, 128, 255)
        # Create items
        items = list()
        items.append(cocos.menu.MenuItem('Attack', on_attack))
        items.append(cocos.menu.MenuItem('Guard', on_guard))
        self.create_menu(items)

class Ally(Combatant):
    def take_turn(self):
        def on_attack():
            enemy = self.battle.enemies[0]
            self.attack(enemy)
            self.battle.remove(menu)
            self.battle.next_turn()
        def on_guard():
            self.heal(self.stats._max_hp * .1)
            self.battle.remove(menu)
            self.battle.next_turn()
        menu = AllyMenu(self, on_attack, on_guard)
        self.battle.add(menu, z=3)

class BattleScene(cocos.scene.Scene):
    def __init__(self):
        super(BattleScene, self).__init__()
        self.background = cocos.sprite.Sprite('background.png', position=(-100,0), anchor=(0,0))
        self.add(self.background)
        # Generate some test combatants
        self.allies = list()
        self.enemies = list()
        self.combatants = list()
        self.ally_layer = cocos.layer.Layer()
        self.enemy_layer = cocos.layer.Layer()
        self.add(self.ally_layer, z=2)
        self.add(self.enemy_layer, z=1)
        for i in range(3):
            ally = Ally('Ally %d' % i, self, 'golem2.png')
            ally.position = (550,i*100+100)
            ally.push_handlers(self)
            self.allies.append(ally)
            self.ally_layer.add(ally)
            enemy = Enemy('Enemy %d' % i, self, 'golem.png')
            enemy.position = (50,i*100+100)
            enemy.push_handlers(self)
            self.enemies.append(enemy)
            self.enemy_layer.add(enemy)
            self.combatants += (ally, enemy)
        self.next_turn()

    def on_damage(self, attacker, defender, damage):
        print "%s deals %d damage to %s!" % (attacker.name, damage, defender.name)

    def on_heal(self, combatant, health):
        print "%s healed %d HP." % (combatant.name, health)

    def on_death(self, combatant):
        print "%s has died." % combatant.name
        if combatant in self.allies:
            self.allies.remove(combatant)
            self.ally_layer.remove(combatant)
        elif combatant in self.enemies:
            self.enemies.remove(combatant)
            self.enemy_layer.remove(combatant)
        self.combatants.remove(combatant)

    def next_turn(self):
        if len(self.allies) == 0:
            print "Enemies win! Tough luck, hero."
            director.pop()
            return
        elif len(self.enemies) == 0:
            print "Allies win! Good work, hero!"
            director.pop()
            return
        # Add combatants speed to their counter
        next_combatant = None
        for combatant in self.combatants:
            combatant.ap += combatant.stats._speed
            if next_combatant == None:
                next_combatant = combatant
            elif combatant.ap > next_combatant.ap:
                next_combatant = combatant
        next_combatant.ap = 0
        print 'Next: %s' % next_combatant.name
        next_combatant.take_turn()

