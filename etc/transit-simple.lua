-- TRANSIT OSRM profile for retro-gtfs project
api_version = 4

Set = require('lib/set')
Sequence = require('lib/sequence')
Handlers = require("lib/way_handlers")
Relations = require("lib/relations")
find_access_tag = require("lib/access").find_access_tag
limit = require("lib/maxspeed").limit
Utils = require("lib/utils")

-- set properties
function setup()
	return {
		properties = {
			weight_name = 'custom'
		},
		-- check these tags for access restrictions, in this order
		access_tags_to_check = {
			'ttc','psv','bus','motor_vehicle','vehicle','access'
		},
		-- 
		access_values_to_accept = Set {
			'yes','designated','destination','permissive'
		},
		-- WHY IS THIS NECESSARY?
		relation_types = Sequence {
			"route"
		}
	}
end

-- process all nodes, really just looking for barriers here
function process_node(profile, node, result, relations)
	-- is this node a barrier?
	local barrier = node:get_value_by_key("barrier")
	if barrier then
		for i, access_tag in ipairs(profile.access_tags_to_check) do
			-- does this access tag exist and have an acceptable value?
			local access_value = node:get_value_by_key(access_tag)
			if access_value and profile.access_values_to_accept[access_value] then 
				-- not a barrier to transit
				print('barrier:',barrier,'access_tag',access_tag,'=',access_value)
				return
			end -- if acceptable access value
		end -- for access tags to check
		-- there was a barrier but we havn't cleared it
		result.barrier = true
	end -- if barrier
end


function process_way(profile, way, result, relations)
	railway = way:get_value_by_key('railway')
	highway = way:get_value_by_key('highway')
	route = way:get_value_by_key('route')
	-- perform a quick initial check and abort if the way is
	-- obviously not routable.
	-- highway or route or railway tags must exist
	if (not highway) and (not route) and (not railway) then
		return
	end
	-- now check for any access tags
	for i, access_tag in ipairs(profile.access_tags_to_check) do
		-- does this access tag exist and have an acceptable value?
		local access_value = way:get_value_by_key(access_tag)
		if access_value and not profile.access_values_to_accept[access_value] then 
			-- not a barrier to transit
			print('denied way with access_tag',access_tag,'=',access_value)
			return 
		end -- if acceptable access value
	end -- for access tags to check
	-- set the default travel mode
	result.forward_mode = mode.driving
	result.backward_mode = mode.driving
	-- set default speeds
	result.forward_speed = 20
	result.backward_speed = 20
	-- set default rates
	result.forward_rate = 5.0
	result.backward_rate = 5.0
	-- set a name
	result.name = way:get_value_by_key('name')
	-- HANDLE ANY RELATION DATA
	-- get a list of relations
	local rel_id_list = relations:get_relations(way)
	-- iterate over them
	for i, rel_id in ipairs(rel_id_list) do
		-- get the relation object
		local rel = relations:relation(rel_id)
		-- find the type of relation
		local reltype = rel:get_value_by_key("type")
		-- is the relation a route?relation
		if reltype == 'route' then
			-- is the route a transit route?
			local route = rel:get_value_by_key("route")
			local route_name = rel:get_value_by_key("name")
			if route and ( route == 'bus' or route == 'tram' ) then
				-- let's be sure we've done something
				local street_name = way:get_value_by_key("name")
				print('route',route_name,'on',street_name)
				-- adjust the weight and rate
				result.forward_speed = 40
				result.backward_speed = 40
				result.forward_rate = 10.0
				result.backward_rate = 10.0
				return result
			end -- if transit route
		end -- if route
	end -- for relation
	return result
end -- way function

function process_turn(profile, turn)
--[[
nothing here for now
--]]
end

return {
  setup = setup,
  process_way = process_way,
  process_node = process_node,
  process_turn = process_turn
}
