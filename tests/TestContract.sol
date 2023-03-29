pragma solidity ^0.8.0;

contract TestEventContract {

	event TestEventOne(uint256 indexed _foo, bytes32 _bar);
	event TestEventTwo(uint256 _foo);

	struct Person {
		string uid;
		address wallet;
	}

	struct Mail {
		Person from;
		Person to;
		string contents;
	}

	function foo(uint256 _foo, bytes32 _bar) public returns (bool) {
		emit TestEventOne(_foo, _bar);
		emit TestEventTwo(_foo);
		return true;
	}

	function foo(Mail memory _mail, uint256 _nonce) public pure returns(string memory) {
		_mail;
		_nonce;
		return _mail.from.uid;
	}
}
