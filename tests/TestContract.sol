pragma solidity ^0.8.0;

contract TestEventContract {

	event TestEventOne(uint256 indexed _foo, bytes32 _bar);
	event TestEventTwo(uint256 _foo);

	function foo(uint256 _foo, bytes32 _bar) public returns (bool) {
		emit TestEventOne(_foo, _bar);
		emit TestEventTwo(_foo);
		return true;
	}
}
