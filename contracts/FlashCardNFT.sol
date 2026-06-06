// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * FlashCardNFT — ERC-1155 for collectible Flash Cards.
 * Each card type has a fixed ID matching the backend flash_cards.id.
 * Using ERC-1155 because multiple users can own the same card type.
 */
contract FlashCardNFT is ERC1155, Ownable {
    mapping(uint256 => uint256) public maxSupply;
    mapping(uint256 => uint256) public totalMinted;
    mapping(uint256 => string)  public cardName;

    event CardMinted(uint256 indexed cardId, address indexed to);
    event CardRegistered(uint256 indexed cardId, string name, uint256 supply);

    constructor() ERC1155("https://api.goatarc.com/cards/{id}.json") Ownable(msg.sender) {}

    function registerCard(uint256 cardId, string calldata name, uint256 supply)
        external onlyOwner
    {
        cardName[cardId]  = name;
        maxSupply[cardId] = supply; // 0 = unlimited
        emit CardRegistered(cardId, name, supply);
    }

    function mint(address to, uint256 cardId, uint256 amount)
        external onlyOwner
    {
        if (maxSupply[cardId] > 0) {
            require(totalMinted[cardId] + amount <= maxSupply[cardId], "Supply exhausted");
        }
        totalMinted[cardId] += amount;
        _mint(to, cardId, amount, "");
        emit CardMinted(cardId, to);
    }

    function setURI(string calldata newuri) external onlyOwner {
        _setURI(newuri);
    }
}
