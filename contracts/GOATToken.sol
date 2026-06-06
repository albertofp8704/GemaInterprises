// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * GOAT Token — in-app currency for GOAT Arc.
 * The backend mints tokens as users earn them; users can bridge
 * in-app balance to on-chain by calling mintTo() from the backend wallet.
 */
contract GOATToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10 ** 18; // 100M tokens

    event Minted(address indexed to, uint256 amount, string reason);

    constructor() ERC20("GOAT Token", "GOAT") Ownable(msg.sender) {}

    function mintTo(address to, uint256 amount, string calldata reason)
        external
        onlyOwner
    {
        require(totalSupply() + amount <= MAX_SUPPLY, "Max supply exceeded");
        _mint(to, amount);
        emit Minted(to, amount, reason);
    }

    function decimals() public pure override returns (uint8) {
        return 18;
    }
}
